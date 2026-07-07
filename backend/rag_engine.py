import os
import json
import math
import sys
import requests

# Fix Windows terminal encoding for Armenian Unicode
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

import os
import json
import math
import sys
import requests

# Fix Windows terminal encoding for Armenian Unicode
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Simple helper to load .env file variables
def load_env():
    for env_path in ["backend/.env", ".env", "../.env"]:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ[k.strip()] = v.strip()
            except:
                pass

# Load environment variables on startup
load_env()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma2")

class RAGEngine:
    def __init__(self):
        self.documents = []
        self.chunks = []
        self.embeddings = [] # list of (chunk_id, vector)
        self.vector_enabled = False
        self.use_gemini = bool(GEMINI_API_KEY)
        
        # Load and index data
        self.load_data()
        self.build_index()

    def load_data(self):
        data_file = "backend/data/mlsa_programs.json"
        if not os.path.exists(data_file):
            print("Data file not found. Running scraper...")
            # Use relative import workaround if needed
            try:
                from scraper import run_scraper
            except ImportError:
                import sys
                sys.path.append(os.path.dirname(__file__))
                from scraper import run_scraper
            run_scraper()
            
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
            print(f"Loaded {len(self.documents)} documents.")
        except Exception as e:
            print(f"Error loading social programs JSON: {e}")
            self.documents = []

    def build_index(self):
        # 1. Create text chunks
        self.chunks = []
        for doc_id, doc in enumerate(self.documents):
            title = doc.get("title", "")
            content = doc.get("content", "")
            
            # Split content by paragraphs or chunks of ~500 chars
            paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
            for p_id, p in enumerate(paragraphs):
                chunk_text = f"Ծրագիր՝ {title}\nՆկարագրություն՝ {p}"
                self.chunks.append({
                    "chunk_id": len(self.chunks),
                    "doc_id": doc_id,
                    "title": title,
                    "text": chunk_text
                })
        print(f"Created {len(self.chunks)} semantic chunks.")

        # 2. Try to generate vector embeddings
        self.embeddings = []
        self.vector_enabled = False
        
        if self.use_gemini:
            print("Using Google Gemini API for embeddings generation...")
            success = True
            for chunk in self.chunks:
                vector = self.get_gemini_embedding(chunk["text"])
                if vector:
                    self.embeddings.append((chunk["chunk_id"], vector))
                else:
                    success = False
                    break
            if success and len(self.embeddings) == len(self.chunks):
                self.vector_enabled = True
                print(f"Gemini Vector search enabled! Generated {len(self.embeddings)} embeddings.")
                return

        # Fallback to local Ollama if Gemini key is missing or failed
        print("Falling back to local Ollama for embeddings...")
        try:
            r = requests.get(OLLAMA_HOST, timeout=3)
            if r.status_code == 200:
                print("Ollama connection successful. Generating embeddings...")
                for chunk in self.chunks:
                    vector = self.get_ollama_embedding(chunk["text"])
                    if vector:
                        self.embeddings.append((chunk["chunk_id"], vector))
                
                if len(self.embeddings) == len(self.chunks):
                    self.vector_enabled = True
                    print(f"Ollama Vector search enabled! Generated {len(self.embeddings)} embeddings.")
                else:
                    print("Could not generate all embeddings. Falling back to keyword search.")
            else:
                print("Ollama returned non-200. Falling back to keyword search.")
        except Exception as e:
            print(f"Ollama not available: {e}. Vector search disabled. Falling back to keyword search.")

    def get_gemini_embedding(self, text):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key={GEMINI_API_KEY}"
            payload = {
                "content": {
                    "parts": [{"text": text}]
                }
            }
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200:
                return r.json().get("embedding", {}).get("values")
            else:
                print(f"Gemini embedding API returned status {r.status_code}: {r.text}")
        except Exception as e:
            print(f"Error calling Gemini Embedding API: {e}")
        return None

    def get_ollama_embedding(self, text):
        try:
            url = f"{OLLAMA_HOST}/api/embeddings"
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": text
            }
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200:
                return r.json().get("embedding")
        except Exception as e:
            print(f"Error generating Ollama embedding: {e}")
        return None

    def cosine_similarity(self, vec1, vec2):
        if not vec1 or not vec2:
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def retrieve(self, query, top_n=3):
        if not self.chunks:
            return []

        # Vector search
        if self.vector_enabled:
            print(f"Performing vector similarity search for: {query}")
            query_vector = self.get_gemini_embedding(query) if self.use_gemini else self.get_ollama_embedding(query)
            if query_vector:
                scores = []
                for chunk_id, vec in self.embeddings:
                    sim = self.cosine_similarity(query_vector, vec)
                    scores.append((chunk_id, sim))
                
                # Sort by similarity score descending
                scores.sort(key=lambda x: x[1], reverse=True)
                top_chunks = scores[:top_n]
                return [self.chunks[cid] for cid, score in top_chunks]

        # Fallback keyword search
        print(f"Performing keyword search for: {query}")
        query_words = set(query.lower().split())
        scores = []
        for chunk in self.chunks:
            chunk_words = chunk["text"].lower().split()
            score = sum(1 for w in query_words if w in chunk_words)
            scores.append((chunk["chunk_id"], score))
            
        scores.sort(key=lambda x: x[1], reverse=True)
        top_chunks = scores[:top_n]
        return [self.chunks[cid] for cid, score in top_chunks]

    def generate_response(self, query, user_lang="hy"):
        # 1. Retrieve relevant contexts
        relevant_chunks = self.retrieve(query, top_n=3)
        context_str = "\n---\n".join([c["text"] for c in relevant_chunks])

        # 2. Build prompt
        if user_lang == "en":
            system_prompt = f"""You are the official Welfare AI Assistant for the Ministry of Labor and Social Affairs (MLSA) of the Republic of Armenia.
Answer the citizen's question politely and accurately using only the provided official social program details.
If the answer cannot be found in the provided context, state that you do not have that specific information.

Context:
{context_str}

Question:
{query}

Answer in English:"""
        else:
            system_prompt = f"""Դուք ՀՀ աշխատանքի և սոցիալական հարցերի նախարարության (MLSA) պաշտոնական AI Օգնականն եք։
Պատասխանեք քաղաքացու հարցին մանրամասն, բարեկիրթ և ճշգրիտ՝ օգտագործելով ՄԻԱՅՆ տրամադրված պաշտոնական ծրագրերի տվյալները։
Եթե հարցի պատասխանը չկա տրամադրված տեղեկատվության մեջ, ասեք, որ չունեք այդ տեղեկատվությունը։

Համատեքստ (Context):
{context_str}

Հարց (Question):
{query}

Պատասխան (հայերեն)՝"""

        # 3. Query Gemini API (Gemma 4 26B model)
        if self.use_gemini:
            print("Querying Google Gemini API (gemma-4-26b-a4b-it)...")
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{
                        "parts": [{"text": system_prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.3
                    }
                }
                r = requests.post(url, json=payload, timeout=60)
                if r.status_code == 200:
                    candidates = r.json().get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        answer = ""
                        for part in parts:
                            # Filter out internal thoughts/reasoning, output only final answer
                            if not part.get("thought", False):
                                answer += part.get("text", "")
                        
                        answer = answer.strip()
                        if answer:
                            return {
                                "answer": answer,
                                "sources": [c["title"] for c in relevant_chunks],
                                "vector_search": self.vector_enabled
                            }
                else:
                    print(f"Gemini API returned status {r.status_code}: {r.text}")
            except Exception as e:
                print(f"Error querying Gemini API: {e}")

        # 4. Fallback to local Ollama
        print("Falling back to local Ollama LLM query...")
        try:
            url = f"{OLLAMA_HOST}/api/generate"
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3
                }
            }
            r = requests.post(url, json=payload, timeout=40)
            if r.status_code == 200:
                answer = r.json().get("response", "").strip()
                return {
                    "answer": answer,
                    "sources": [c["title"] for c in relevant_chunks],
                    "vector_search": self.vector_enabled
                }
        except Exception as e:
            print(f"Error querying Ollama LLM: {e}")
            
        # Fallback default response if both fail
        if user_lang == "en":
            return {
                "answer": "Sorry, the AI Assistant is currently experiencing connection issues. Please make sure the backend is active.",
                "sources": [],
                "vector_search": False
            }
        else:
            return {
                "answer": "Ցավոք, AI Օգնականի հետ կապը ժամանակավորապես անհասանելի է: Խնդրում ենք համոզվել, որ սերվերն ակտիվ է:",
                "sources": [],
                "vector_search": False
            }

if __name__ == "__main__":
    engine = RAGEngine()
    test_q = "մինչև 2 տարեկան երեխայի նպաստ"
    res = engine.generate_response(test_q)
    print(json.dumps(res, ensure_ascii=False, indent=2))


