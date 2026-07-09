"""
WISE Foundation — MLSA Social Programs RAG Engine
Hybrid vector + keyword retrieval over citizen summaries and ARLIS legal acts.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
from collections import defaultdict
from typing import Any

import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def load_env():
    for env_path in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        "backend/.env",
        ".env",
        "../.env",
    ]:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip())
            except Exception:
                pass


load_env()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma2")
# Prefer stable Gemini models first; Gemma experimental last
GEMINI_GENERATE_MODELS = [
    m.strip()
    for m in os.environ.get(
        "GEMINI_GENERATE_MODELS",
        "gemini-2.5-flash,gemini-flash-latest,gemini-2.5-flash-lite,gemma-4-26b-a4b-it,gemma-4-31b-it",
    ).split(",")
    if m.strip()
]
GEMINI_MAX_RETRIES = int(os.environ.get("GEMINI_MAX_RETRIES", "2"))

LEGAL_QUERY_HINTS = (
    "իրավունք", "չափորոշիչ", "հոդված", "մերժում", "ստաժ", "կարգ", "որոշում",
    "օրենք", "պահանջ", "փաստաթղթ", "eligibility", "criteria", "article", "reject",
    "document", "law", "procedure",
)
SUMMARY_QUERY_HINTS = (
    "որքան", "ինչքան", "ինչպես դիմել", "որտեղ", "պարզ", "կարճ", "how much",
    "how to apply", "where", "simple", "amount", "documents needed",
)


class RAGEngine:
    def __init__(self):
        self.documents: list[dict[str, Any]] = []
        self.chunks: list[dict[str, Any]] = []
        self.embeddings: list[tuple[int, list[float]]] = []
        self.vector_enabled = False
        self.use_gemini = bool(GEMINI_API_KEY)
        self.corpus_hash = ""
        self.legal_acts = 0
        self.cache_ok = False

        self.load_data()
        self.build_index()

    def _backend_dir(self) -> str:
        return os.path.dirname(os.path.abspath(__file__))

    def load_data(self):
        data_file = os.path.join(self._backend_dir(), "data", "mlsa_programs.json")
        if not os.path.exists(data_file):
            print("Data file not found. Running scraper...")
            try:
                from scraper import run_scraper
            except ImportError:
                sys.path.append(self._backend_dir())
                from scraper import run_scraper
            run_scraper()

        try:
            with open(data_file, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
            # Normalize legacy plain summaries
            for doc in self.documents:
                doc.setdefault("doc_type", "summary")
                doc.setdefault("act_id", None)
                doc.setdefault("article", None)
                doc.setdefault("category", "general")
                doc.setdefault("program_keys", [])
                doc.setdefault("source_url", None)
                doc.setdefault("priority", 2)
            self.legal_acts = len({d.get("act_id") for d in self.documents if d.get("act_id")})
            print(f"Loaded {len(self.documents)} documents ({self.legal_acts} legal acts).")
        except Exception as e:
            print(f"Error loading social programs JSON: {e}")
            self.documents = []

    def build_index(self):
        self.chunks = []
        for doc_id, doc in enumerate(self.documents):
            title = doc.get("title", "")
            content = doc.get("content", "")
            doc_type = doc.get("doc_type", "summary")
            if not content:
                continue

            # Keep one coherent unit per summary; legal acts already article-sized
            if doc_type == "legal":
                pieces = [content]
            else:
                pieces = [content.strip()] if content.strip() else []

            for p in pieces:
                if doc_type == "legal":
                    chunk_text = f"Ակտ՝ {title}\n{p}"
                else:
                    chunk_text = f"Ծրագիր՝ {title}\nՆկարագրություն՝ {p}"

                self.chunks.append({
                    "chunk_id": len(self.chunks),
                    "doc_id": doc_id,
                    "title": title,
                    "text": chunk_text,
                    "doc_type": doc_type,
                    "act_id": doc.get("act_id"),
                    "article": doc.get("article"),
                    "category": doc.get("category"),
                    "source_url": doc.get("source_url"),
                    "priority": doc.get("priority", 2),
                })

        print(f"Created {len(self.chunks)} semantic chunks.")
        self.corpus_hash = hashlib.sha256(
            json.dumps(
                [{"t": c["title"], "x": c["text"][:200]} for c in self.chunks],
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()[:16]

        self._load_or_build_embeddings()

    def _cache_path(self) -> str:
        return os.path.join(self._backend_dir(), "data", "embeddings_cache.json")

    def _load_or_build_embeddings(self):
        self.embeddings = []
        self.vector_enabled = False
        self.cache_ok = False
        cache_file = self._cache_path()

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if (
                    cached.get("corpus_hash") == self.corpus_hash
                    and cached.get("chunks_count") == len(self.chunks)
                ):
                    self.embeddings = [
                        (item["chunk_id"], item["vector"])
                        for item in cached.get("embeddings", [])
                    ]
                    if len(self.embeddings) == len(self.chunks):
                        self.vector_enabled = True
                        self.cache_ok = True
                        print(f"Loaded {len(self.embeddings)} embeddings from cache (hash={self.corpus_hash}).")
                        return
            except Exception as e:
                print(f"Error loading embeddings cache: {e}")

        force_embed = os.environ.get("FORCE_EMBED", "").strip() in ("1", "true", "yes")
        # Large ARLIS corpora: skip online bulk embed unless forced or small index
        if len(self.chunks) > 200 and not force_embed:
            print(
                f"Skipping bulk embedding for {len(self.chunks)} chunks "
                "(set FORCE_EMBED=1 to build full vector cache). Using keyword hybrid."
            )
            return

        if self.use_gemini:
            print("Using Google Gemini API for embeddings…")
            success = True
            for i, chunk in enumerate(self.chunks):
                if i and i % 25 == 0:
                    print(f"  … embedded {i}/{len(self.chunks)}")
                vector = self.get_gemini_embedding(chunk["text"])
                if vector:
                    self.embeddings.append((chunk["chunk_id"], vector))
                else:
                    success = False
                    break
            if success and len(self.embeddings) == len(self.chunks):
                self.vector_enabled = True
                self._save_embeddings_cache()
                print(f"Gemini vector search enabled ({len(self.embeddings)} embeddings).")
                return
            print("Gemini embeddings incomplete; trying Ollama…")
            self.embeddings = []

        print("Falling back to local Ollama for embeddings…")
        try:
            r = requests.get(OLLAMA_HOST, timeout=3)
            if r.status_code == 200:
                for i, chunk in enumerate(self.chunks):
                    if i and i % 25 == 0:
                        print(f"  … embedded {i}/{len(self.chunks)}")
                    vector = self.get_ollama_embedding(chunk["text"])
                    if vector:
                        self.embeddings.append((chunk["chunk_id"], vector))
                if len(self.embeddings) == len(self.chunks):
                    self.vector_enabled = True
                    self._save_embeddings_cache()
                    print(f"Ollama vector search enabled ({len(self.embeddings)} embeddings).")
                else:
                    print("Could not generate all embeddings. Keyword search only.")
            else:
                print("Ollama non-200. Keyword search only.")
        except Exception as e:
            print(f"Ollama not available: {e}. Keyword search only.")

    def _save_embeddings_cache(self):
        try:
            cache_file = self._cache_path()
            payload = {
                "corpus_hash": self.corpus_hash,
                "chunks_count": len(self.chunks),
                "embeddings": [
                    {"chunk_id": cid, "vector": vec} for cid, vec in self.embeddings
                ],
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            self.cache_ok = True
            print("Saved embeddings cache.")
        except Exception as e:
            print(f"Error saving embeddings cache: {e}")

    def get_gemini_embedding(self, text: str):
        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-embedding-2:embedContent?key={GEMINI_API_KEY}"
            )
            payload = {"content": {"parts": [{"text": text[:8000]}]}}
            r = requests.post(url, json=payload, timeout=20)
            if r.status_code == 200:
                return r.json().get("embedding", {}).get("values")
            print(f"Gemini embedding status {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"Gemini embedding error: {e}")
        return None

    def get_ollama_embedding(self, text: str):
        try:
            url = f"{OLLAMA_HOST}/api/embeddings"
            payload = {"model": OLLAMA_MODEL, "prompt": text[:8000]}
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 200:
                return r.json().get("embedding")
        except Exception as e:
            print(f"Ollama embedding error: {e}")
        return None

    @staticmethod
    def cosine_similarity(vec1, vec2) -> float:
        if not vec1 or not vec2:
            return 0.0
        n = min(len(vec1), len(vec2))
        v1, v2 = vec1[:n], vec2[:n]
        dot = sum(a * b for a, b in zip(v1, v2))
        na = math.sqrt(sum(a * a for a in v1))
        nb = math.sqrt(sum(b * b for b in v2))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)

    def _tokenize(self, text: str) -> set[str]:
        text = text.lower()
        # Keep Armenian letters and alphanumerics
        words = re.findall(r"[\w\u0531-\u0587]+", text, flags=re.UNICODE)
        return {w for w in words if len(w) > 2}

    def _keyword_scores(self, query: str) -> list[tuple[int, float]]:
        q_words = self._tokenize(query)
        if not q_words:
            return []
        scores = []
        for chunk in self.chunks:
            text = chunk["text"] or ""
            c_words = self._tokenize(text)
            if not c_words:
                continue
            overlap = len(q_words & c_words)
            # Substring fallback for Armenian morphology (նպաստ / նպաստի)
            sub_hits = 0
            low = text.lower()
            for w in q_words:
                if len(w) >= 4 and w in low:
                    sub_hits += 1
            title_words = self._tokenize(chunk.get("title") or "")
            title_hit = len(q_words & title_words)
            # Soft length normalization — avoid crushing long legal articles
            length_norm = max(2.0, min(math.log(1 + len(c_words)), 6.5))
            score = (float(overlap) + 0.65 * float(sub_hits)) / length_norm
            score += 2.2 * float(title_hit)
            # Prefer denser matches
            if overlap >= 2:
                score += 0.35 * (overlap - 1)
            if score > 0:
                scores.append((chunk["chunk_id"], score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def _vector_scores(self, query: str) -> list[tuple[int, float]]:
        if not self.vector_enabled:
            return []
        q_vec = (
            self.get_gemini_embedding(query)
            if self.use_gemini
            else self.get_ollama_embedding(query)
        )
        if not q_vec:
            return []
        scores = []
        for chunk_id, vec in self.embeddings:
            sim = self.cosine_similarity(q_vec, vec)
            scores.append((chunk_id, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def _query_prefers_legal(self, query: str) -> bool:
        q = query.lower()
        return any(h in q for h in LEGAL_QUERY_HINTS)

    def _query_prefers_summary(self, query: str) -> bool:
        q = query.lower()
        return any(h in q for h in SUMMARY_QUERY_HINTS)

    def _merge_rank(self, query: str, top_n: int = 8) -> list[dict[str, Any]]:
        """Hybrid retrieval with diversification by act_id / title."""
        vec = self._vector_scores(query)
        kw = self._keyword_scores(query)

        # Normalize scores to 0-1 within each channel
        def normalize(pairs: list[tuple[int, float]]) -> dict[int, float]:
            if not pairs:
                return {}
            mx = max(s for _, s in pairs) or 1.0
            mn = min(s for _, s in pairs)
            span = (mx - mn) or 1.0
            return {cid: (s - mn) / span for cid, s in pairs}

        vmap = normalize(vec[:40])
        kmap = normalize(kw[:40])
        all_ids = set(vmap) | set(kmap)

        prefer_legal = self._query_prefers_legal(query)
        prefer_summary = self._query_prefers_summary(query)

        combined: list[tuple[int, float]] = []
        for cid in all_ids:
            score = 0.55 * vmap.get(cid, 0.0) + 0.45 * kmap.get(cid, 0.0)
            chunk = self.chunks[cid]
            # Metadata boosts
            if prefer_legal and chunk.get("doc_type") == "legal":
                score += 0.22
            if prefer_summary and chunk.get("doc_type") == "summary":
                score += 0.18
            if chunk.get("doc_type") == "summary" and not prefer_legal:
                score += 0.06
            if chunk.get("doc_type") == "legal" and prefer_legal is False and prefer_summary is False:
                score += 0.04
            # Slight priority boost for core acts
            pr = chunk.get("priority") or 2
            score += max(0, (3 - pr)) * 0.02
            combined.append((cid, score))

        combined.sort(key=lambda x: x[1], reverse=True)

        # Diversify: limit chunks per act / per title; mix summary + legal
        picked: list[dict[str, Any]] = []
        act_counts: dict[str, int] = defaultdict(int)
        title_counts: dict[str, int] = defaultdict(int)
        type_counts: dict[str, int] = defaultdict(int)

        def try_pick(cid: int) -> bool:
            chunk = self.chunks[cid]
            act_key = str(chunk.get("act_id") or f"t:{chunk.get('title')}" or cid)
            title_key = chunk.get("title") or str(cid)
            dtype = chunk.get("doc_type") or "summary"
            if act_counts[act_key] >= 2:
                return False
            if title_counts[title_key] >= 1:
                return False
            # Keep room for both layers
            if type_counts[dtype] >= max(3, top_n // 2 + 1):
                return False
            picked.append(chunk)
            act_counts[act_key] += 1
            title_counts[title_key] += 1
            type_counts[dtype] += 1
            return True

        for cid, _ in combined:
            try_pick(cid)
            if len(picked) >= top_n:
                break

        # Ensure at least one legal + one summary when available in candidates
        have_legal = any(c.get("doc_type") == "legal" for c in picked)
        have_sum = any(c.get("doc_type") == "summary" for c in picked)
        if not have_legal or not have_sum:
            for cid, _ in combined:
                chunk = self.chunks[cid]
                if not have_legal and chunk.get("doc_type") == "legal":
                    if try_pick(cid):
                        have_legal = True
                if not have_sum and chunk.get("doc_type") == "summary":
                    if try_pick(cid):
                        have_sum = True
                if have_legal and have_sum:
                    break
            # Trim if we overshot
            if len(picked) > top_n:
                picked = picked[:top_n]

        # Fallback pure keyword if hybrid empty
        if not picked:
            for cid, _ in kw[:top_n]:
                picked.append(self.chunks[cid])

        return picked

    def retrieve(self, query: str, top_n: int = 8) -> list[dict[str, Any]]:
        if not self.chunks:
            return []
        if self.vector_enabled:
            print(f"Hybrid retrieval for: {query}")
        else:
            print(f"Keyword retrieval for: {query}")
        return self._merge_rank(query, top_n=top_n)

    def _build_sources(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        sources = []
        for c in chunks:
            key = (c.get("title"), c.get("article"), c.get("act_id"))
            if key in seen:
                continue
            seen.add(key)
            act_id = c.get("act_id")
            url = c.get("source_url")
            if act_id and not url:
                url = f"https://www.arlis.am/hy/acts/{act_id}"
            sources.append({
                "title": c.get("title") or "Source",
                "act_id": act_id,
                "url": url,
                "article": c.get("article"),
                "doc_type": c.get("doc_type"),
            })
        return sources[:8]

    def _follow_ups(self, query: str, lang: str, chunks: list[dict[str, Any]]) -> list[str]:
        cats = {c.get("category") for c in chunks if c.get("category")}
        if lang == "en":
            base = [
                "Who is eligible?",
                "What documents are required?",
                "How and where do I apply?",
                "What is the amount?",
            ]
            if "pensions" in cats:
                base.append("What is the minimum work history?")
            if "employment" in cats:
                base.append("How do I register as unemployed?")
            return base[:4]
        base = [
            "Ո՞վ ունի իրավունք",
            "Ի՞նչ փաստաթղթեր են պետք",
            "Ինչպե՞ս և որտե՞ղ դիմել",
            "Որքա՞ն է չափը",
        ]
        if "pensions" in cats:
            base.append("Որքա՞ն է նվազագույն ստաժը")
        if "employment" in cats:
            base.append("Ինչպե՞ս ձևակերպել գործազրկության կարգավիճակ")
        return base[:4]

    def _prompt(self, query: str, context_str: str, user_lang: str) -> str:
        if user_lang == "en":
            return f"""You are the official WISE / MLSA citizen assistant for social programs in Armenia.
Answer ONLY using the provided context (citizen program summaries and official ARLIS legal excerpts).
Be warm, clear, and practical — not legalese-only. Never invent amounts, eligibility rules, or procedures.
Prefer concrete numbers, document lists, and steps when they appear in the context.
If something is missing from the context, say so and suggest contacting Unified Social Service (hotline 114) or e-soc.am.
Do not invent ARLIS article numbers.

Structure your answer with markdown headings when relevant:
## Short answer
## Who is eligible
## Amount / calculation
## Required documents
## How / where to apply
## Deadlines
## Sources
(Skip sections that are not applicable. Keep language simple. Use short bullet lists.)

Context:
{context_str}

Citizen question:
{query}

Answer in clear English:"""

        return f"""Դուք WISE / ՀՀ ԱՍՀՆ քաղաքացիական AI օգնականն եք սոցիալական ծրագրերի վերաբերյալ։
Պատասխանեք ՄԻԱՅՆ տրամադրված համատեքստից (քաղաքացիական ամփոփումներ և ARLIS պաշտոնական իրավական հատվածներ)։
Լինեք ջերմ, պարզ և գործնական — խուսափեք չոր իրավաբանական լեզվից։ Երբեք մի հորինեք գումարներ, չափորոշիչներ կամ ընթացակարգեր։
Եթե համատեքստում կան կոնկրետ թվեր, փաստաթղթերի ցանկեր կամ քայլեր — ներառեք դրանք։
Եթե տեղեկատվությունը բավարար չէ, ասեք դա և առաջարկեք դիմել Միասնական սոցիալական ծառայություն (թեժ գիծ 114) կամ e-soc.am։
Մի հորինեք հոդվածների համարներ։

Պատասխանը կառուցեք markdown վերնագրերով (բաց թողեք անկիրառելի բաժինները)՝
## Կարճ պատասխան
## Ով ունի իրավունք
## Չափ / հաշվարկ
## Անհրաժեշտ փաստաթղթեր
## Ինչպես և որտեղ դիմել
## Ժամկետներ
## Աղբյուրներ
(Օգտագործեք կարճ ցուցակներ։)

Համատեքստ.
{context_str}

Քաղաքացու հարց.
{query}

Պատասխանը պարզ հայերենով՝"""

    def _parse_gemini_answer(self, data: dict) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        answer = ""
        for part in parts:
            if not part.get("thought", False):
                answer += part.get("text", "")
        return answer.strip()

    def _generate_with_gemini(self, system_prompt: str) -> str:
        """Try multiple Gemini models with light retries on 5xx/timeouts."""
        if not self.use_gemini:
            return ""
        payload = {
            "contents": [{"parts": [{"text": system_prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048,
            },
        }
        for model in GEMINI_GENERATE_MODELS:
            for attempt in range(1, GEMINI_MAX_RETRIES + 1):
                try:
                    print(f"Querying Gemini model={model} attempt={attempt}…")
                    url = (
                        f"https://generativelanguage.googleapis.com/v1beta/models/"
                        f"{model}:generateContent?key={GEMINI_API_KEY}"
                    )
                    r = requests.post(url, json=payload, timeout=75)
                    if r.status_code == 200:
                        answer = self._parse_gemini_answer(r.json())
                        if answer:
                            print(f"Gemini OK via {model}")
                            return answer
                        print(f"Gemini {model}: empty candidates")
                    elif r.status_code in (429, 500, 502, 503, 504):
                        print(f"Gemini {model} status {r.status_code}; retrying…")
                        continue
                    else:
                        print(f"Gemini {model} status {r.status_code}: {r.text[:220]}")
                        break  # non-retryable for this model
                except requests.Timeout:
                    print(f"Gemini {model} timeout on attempt {attempt}")
                except Exception as e:
                    print(f"Gemini {model} error: {e}")
                    break
        return ""

    def _generate_with_ollama(self, system_prompt: str) -> str:
        print("Falling back to local Ollama…")
        try:
            url = f"{OLLAMA_HOST}/api/generate"
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": system_prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            }
            r = requests.post(url, json=payload, timeout=60)
            if r.status_code == 200:
                return (r.json().get("response") or "").strip()
            print(f"Ollama status {r.status_code}")
        except Exception as e:
            print(f"Ollama generate error: {e}")
        return ""

    def generate_response(self, query: str, user_lang: str = "hy") -> dict[str, Any]:
        relevant = self.retrieve(query, top_n=8)
        context_parts = []
        for c in relevant:
            src = c.get("source_url") or ""
            art = c.get("article") or ""
            header = f"[{c.get('doc_type', 'doc')}] {c.get('title', '')}"
            if art:
                header += f" | {art}"
            if src:
                header += f" | {src}"
            context_parts.append(f"{header}\n{c['text']}")
        context_str = "\n\n---\n\n".join(context_parts) if context_parts else "(no context)"

        system_prompt = self._prompt(query, context_str, user_lang)
        sources = self._build_sources(relevant)
        follow_ups = self._follow_ups(query, user_lang, relevant)

        # Gemini multi-model generation with retries
        if self.use_gemini:
            answer = self._generate_with_gemini(system_prompt)
            if answer:
                return {
                    "answer": answer,
                    "sources": sources,
                    "vector_search": self.vector_enabled,
                    "follow_ups": follow_ups,
                }

        # Ollama fallback
        answer = self._generate_with_ollama(system_prompt)
        if answer:
            return {
                "answer": answer,
                "sources": sources,
                "vector_search": self.vector_enabled,
                "follow_ups": follow_ups,
            }

        # Extractive fallback from retrieved corpus (works offline without LLM)
        if relevant:
            answer = self._extractive_answer(query, relevant, user_lang)
            return {
                "answer": answer,
                "sources": sources,
                "vector_search": self.vector_enabled,
                "follow_ups": follow_ups,
            }

        if user_lang == "en":
            return {
                "answer": (
                    "Sorry, no matching program information was found. "
                    "Please call Unified Social Service hotline 114 or visit e-soc.am."
                ),
                "sources": sources,
                "vector_search": False,
                "follow_ups": follow_ups,
            }
        return {
            "answer": (
                "Ցավոք, համապատասխան տեղեկատվություն չի գտնվել։ "
                "Խնդրում ենք զանգահարել ՄՍԾ թեժ գիծ 114 կամ այցելել e-soc.am։"
            ),
            "sources": sources,
            "vector_search": False,
            "follow_ups": follow_ups,
        }

    def _extractive_answer(
        self, query: str, chunks: list[dict[str, Any]], user_lang: str
    ) -> str:
        """Plain structured answer from top chunks when LLM is offline."""
        primary = chunks[0]
        body = (primary.get("text") or "")[:1200]
        # Drop label prefixes for readability
        body = re.sub(r"^(Ծրագիր|Ակտ|Նկարագրություն)՝\s*", "", body, flags=re.M)
        more_titles = []
        for c in chunks[1:4]:
            t = c.get("title")
            if t and t not in more_titles:
                more_titles.append(t)

        if user_lang == "en":
            parts = [
                "## Short answer",
                f"Based on official program materials related to your question **«{query}»**:",
                "",
                body.strip(),
            ]
            if more_titles:
                parts += ["", "## Related sources", *[f"- {t}" for t in more_titles]]
            parts += [
                "",
                "## How / where to apply",
                "- Online: e-soc.am",
                "- In person: Unified Social Service territorial centers",
                "- Hotline: **114**",
                "",
                "_Note: generative AI is offline; this is an extract from the local legal/program index._",
            ]
            return "\n".join(parts)

        parts = [
            "## Կարճ պատասխան",
            f"Ձեր հարցին (**«{query}»**) առնչվող պաշտոնական նյութերից.",
            "",
            body.strip(),
        ]
        if more_titles:
            parts += ["", "## Կապված աղբյուրներ", *[f"- {t}" for t in more_titles]]
        parts += [
            "",
            "## Ինչպես և որտեղ դիմել",
            "- Առցանց՝ e-soc.am",
            "- Անձամբ՝ Միասնական սոցիալական ծառայության տարածքային կենտրոն",
            "- Թեժ գիծ՝ **114**",
            "",
            "_Նշում. գեներատիվ AI-ն անհասանելի է. սա քաղվածք է տեղական իրավական/ծրագրային բազայից._",
        ]
        return "\n".join(parts)


if __name__ == "__main__":
    engine = RAGEngine()
    res = engine.generate_response("ընտանեկան նպաստ չափորոշիչներ")
    print(json.dumps(res, ensure_ascii=False, indent=2)[:2000])
