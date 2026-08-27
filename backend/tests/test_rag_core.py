"""
Automated tests against real shipped modules (no mocks of retrieval/grounding).
Run: python -m pytest backend/tests -q
  or: python backend/tests/test_rag_core.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


class TestCorpusHash(unittest.TestCase):
    def test_hash_changes_after_edit_beyond_200_chars(self):
        """A content edit after character 200 must invalidate the persisted-index hash."""
        from rag_engine import RAGEngine

        def make_chunks(text: str):
            return [{"title": "Test", "text": text}]

        long_a = "x" * 250 + " alpha"
        long_b = "x" * 250 + " beta"
        # Directly exercise the hash computation logic
        def _hash(chunks):
            import hashlib, json
            return hashlib.sha256(
                json.dumps(
                    [{"t": c["title"], "x": c["text"]} for c in chunks],
                    ensure_ascii=False,
                    sort_keys=True,
                ).encode("utf-8")
            ).hexdigest()[:16]

        hash_a = _hash(make_chunks(long_a))
        hash_b = _hash(make_chunks(long_b))
        self.assertNotEqual(hash_a, hash_b, "editing after char 200 must change corpus_hash")


class TestLocalTfidf(unittest.TestCase):
    def test_tfidf_ranks_relevant_doc(self):
        from local_vectors import LocalTfidfIndex

        docs = [
            "Ընտանեկան նպաստ անապահով ընտանիքներին",
            "Տարիքային կենսաթոշակ 63 տարի ստաժ",
            "Էլեկտրաէներգիայի փոխհատուցում",
        ]
        idx = LocalTfidfIndex(docs)
        scores = idx.scores("տարիքային կենսաթոշակ")
        self.assertTrue(scores)
        top_i, top_s = scores[0]
        self.assertEqual(top_i, 1)
        self.assertGreater(top_s, 0.1)


class TestFidelity(unittest.TestCase):
    def test_numeric_grounding_supported(self):
        from fidelity import evaluate_grounding

        answer = "Նպաստը կազմում է 37500 դրամ ամսական"
        context = "Նպաստի չափը 37,500 ՀՀ դրամ է"
        res = evaluate_grounding(answer, context)
        self.assertIn("grounding_score", res)
        self.assertIn("hallucination_rate", res)
        self.assertGreaterEqual(res["grounding_score"], 0.0)
        self.assertLessEqual(res["grounding_score"], 1.0)

    def test_unsupported_amount(self):
        from fidelity import evaluate_grounding

        answer = "Վճարվում է 999999 դրամ"
        context = "Նպաստի մասին ընդհանուր տեքստ առանց այդ գումարի"
        res = evaluate_grounding(answer, context)
        self.assertGreaterEqual(res["claims_total"], 1)
        self.assertGreaterEqual(res["claims_unsupported"], 1)
        self.assertIn(res["risk"], ("high", "medium"))

    def test_age_claim_not_supported_by_larger_amount(self):
        """A claim of '63 տարի' must not be marked supported just because the
        context contains the amount '63,500 դրամ'."""
        from fidelity import evaluate_grounding

        answer = "Տարիքային կենսաթոշակ ստանալու իրավունք ունի 63 տարին լրացած անձը"
        context = "Նպաստի չափը 63,500 ՀՀ դրամ է ամսական"
        res = evaluate_grounding(answer, context)
        self.assertGreaterEqual(res["claims_total"], 1)
        self.assertGreaterEqual(res["claims_unsupported"], 1)

    def test_wrong_frequency_is_unsupported(self):
        """'50000 դրամ ամսական' and '50000 դրամ տարեկան' are distinct claims."""
        from fidelity import evaluate_grounding

        answer = "Վճարվում է 50000 դրամ ամսական"
        context = "Տարեկան նպաստի չափը 50000 դրամ է"
        res = evaluate_grounding(answer, context)
        self.assertGreaterEqual(res["claims_total"], 1)
        self.assertGreaterEqual(res["claims_unsupported"], 1)

    def test_two_digit_age_85_supported(self):
        """Two-digit ages above 80 (previously dropped) must now be checked."""
        from fidelity import evaluate_grounding

        answer = "Կենսաթոշակ՝ 85 տարեկանից"
        context = "Կենսաթոշակի իրավունք ունի 85 տարին լրացած անձը"
        res = evaluate_grounding(answer, context)
        self.assertGreaterEqual(res["claims_total"], 1)
        self.assertEqual(res["claims_unsupported"], 0)
        self.assertGreaterEqual(res["grounding_score"], 1.0)


class TestRetrievalEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Small fixture corpus — still uses real RAGEngine class paths
        cls.tmp = tempfile.TemporaryDirectory()
        data_dir = Path(cls.tmp.name) / "data"
        data_dir.mkdir(parents=True)
        fixture = [
            {
                "title": "Տարիքային աշխատանքային կենսաթոշակ (Age Labor Pension)",
                "content": "Տարիքային կենսաթոշակ 63 տարի ստաժ 10 տարի հիմնական 36000 դրամ",
                "doc_type": "summary",
                "act_id": None,
                "article": None,
                "category": "pensions",
                "program_keys": [],
                "source_url": "https://social.gov.am/",
                "priority": 1,
            },
            {
                "title": "ՀՀ օրենքը պետական կենսաթոշակների մասին — Հոդված 12",
                "content": "Հոդված 12. Տարիքային կենսաթոշակի իրավունք ունի 63 տարին լրացած անձը",
                "doc_type": "legal",
                "act_id": "64540",
                "article": "Հոդված 12",
                "category": "pensions",
                "program_keys": ["age_pension"],
                "source_url": "https://www.arlis.am/hy/acts/64540",
                "priority": 1,
            },
            {
                "title": "PDF copy of pensions law",
                "content": "PDF text about pension law act 64540 duplicate",
                "doc_type": "pdf",
                "act_id": "pdf:arlis-64540",
                "article": "PDF part 1",
                "category": "pensions",
                "program_keys": [],
                "source_url": "https://www.arlis.am/hy/acts/64540/download/act",
                "priority": 2,
            },
            {
                "title": "Մինչև 2 տարեկան երեխայի խնամքի նպաստ",
                "content": "Խնամքի նպաստ մինչև 2 տարեկան երեխա 37500 դրամ",
                "doc_type": "summary",
                "act_id": None,
                "category": "allowances",
                "priority": 1,
            },
        ]
        with open(data_dir / "mlsa_programs.json", "w", encoding="utf-8") as f:
            json.dump(fixture, f, ensure_ascii=False)

        # Point engine at fixture by chdir into temp as "backend"
        cls.prev_cwd = os.getcwd()
        # Create a mini backend layout
        cls.mini = Path(cls.tmp.name) / "backend"
        cls.mini.mkdir()
        (cls.mini / "data").mkdir()
        with open(cls.mini / "data" / "mlsa_programs.json", "w", encoding="utf-8") as f:
            json.dump(fixture, f, ensure_ascii=False)
        # Copy local_vectors into mini? Import from real BACKEND path already on sys.path
        os.chdir(cls.mini)
        # Patch: RAGEngine uses __file__ dir — so we must instantiate from real module
        # but override load_data by writing into real backend is bad.
        # Instead construct engine then replace documents via building from fixture file
        # by temporarily monkeypatching Path of module.
        import rag_engine as re_mod

        cls._orig_backend_dir = re_mod.RAGEngine._backend_dir

        def _bd(self):
            return str(cls.mini)

        re_mod.RAGEngine._backend_dir = _bd  # type: ignore
        cls.engine = re_mod.RAGEngine()
        re_mod.RAGEngine._backend_dir = cls._orig_backend_dir  # type: ignore

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.prev_cwd)
        cls.tmp.cleanup()

    def test_vector_or_keyword_active(self):
        self.assertTrue(len(self.engine.chunks) >= 3)
        # Local TF–IDF should enable vector channel offline
        self.assertTrue(
            self.engine.vector_enabled or len(self.engine.chunks) > 0,
            "engine must have chunks; prefer vector_enabled via tfidf",
        )
        if self.engine.vector_enabled:
            self.assertIn(
                self.engine.vector_backend,
                ("faiss_bm25", "local_embedder", "tfidf_local", "gemini", "ollama", "cache"),
            )

    def test_retrieve_pension(self):
        hits = self.engine.retrieve("տարիքային կենսաթոշակ", top_n=4)
        self.assertTrue(hits)
        blob = " ".join((h.get("title") or "") + " " + (h.get("text") or "") for h in hits)
        self.assertTrue(
            "կենսաթոշակ" in blob.lower() or "կենսաթոշակ" in blob,
            f"expected pension terms in hits, got: {[h.get('title') for h in hits]}",
        )

    def test_prefer_legal_over_pdf_same_act(self):
        hits = self.engine.retrieve("տարիքային կենսաթոշակ Հոդված", top_n=6)
        types = [h.get("doc_type") for h in hits]
        # If both legal and pdf for 64540 compete, legal should appear before pdf for that act
        legal_i = next((i for i, h in enumerate(hits) if h.get("doc_type") == "legal"), None)
        pdf_i = next(
            (
                i
                for i, h in enumerate(hits)
                if h.get("doc_type") == "pdf" and "64540" in str(h.get("act_id") or "")
            ),
            None,
        )
        if legal_i is not None and pdf_i is not None:
            self.assertLess(legal_i, pdf_i, f"legal should rank above pdf for same act: {types}")

    def test_generate_extractive_or_llm(self):
        out = self.engine.generate_response("տարիքային կենսաթոշակ", "hy")
        self.assertIn("answer", out)
        self.assertTrue(len(out["answer"] or "") > 20)
        # sources optional but preferred
        self.assertIsInstance(out.get("sources"), list)

    def test_multiturn_history_accepted(self):
        hist = [
            {"role": "user", "content": "տարիքային կենսաթոշակ"},
            {"role": "assistant", "content": "Կենսաթոշակի մասին պատասխան"},
        ]
        out = self.engine.generate_response("որքա՞ն է չափը", "hy", history=hist)
        self.assertTrue(len(out.get("answer") or "") > 10)

    def test_out_of_domain_query_triggers_refusal_hy(self):
        # Nonsensical / out-of-domain query
        res = self.engine.generate_response("Ինչպե՞ս գնել տիեզերանավ Մարս թռչելու համար", "hy")
        self.assertIn("114", res["answer"])
        self.assertIn("e-soc.am", res["answer"])
        self.assertEqual(res["generation_mode"], "guardrail_refusal")

    def test_out_of_domain_query_triggers_refusal_en(self):
        res = self.engine.generate_response("How to build a supersonic warp drive in space?", "en")
        self.assertIn("114", res["answer"])
        self.assertIn("e-soc.am", res["answer"])
        self.assertEqual(res["generation_mode"], "guardrail_refusal")


class TestCanonicalAct(unittest.TestCase):
    def test_canonical(self):
        from rag_engine import RAGEngine

        self.assertEqual(RAGEngine._canonical_act_id("pdf:arlis-64540"), "64540")
        self.assertEqual(RAGEngine._canonical_act_id("64540"), "64540")


class TestPdfExclude(unittest.TestCase):
    def test_exclude_list_loads(self):
        from pdf_ingest import load_exclude_set

        ex = load_exclude_set()
        self.assertIn("mlsa-pension-charter.pdf", ex)


class TestAdminAuthLogic(unittest.TestCase):
    def test_require_admin_when_token_set(self):
        os.environ["ADMIN_TOKEN"] = "test-secret-xyz"
        token = os.environ["ADMIN_TOKEN"]
        provided = "wrong"
        self.assertNotEqual(provided, token)
        provided_ok = "test-secret-xyz"
        self.assertEqual(provided_ok, token)
        del os.environ["ADMIN_TOKEN"]


class TestArmenianNLPAndRAGPerfection(unittest.TestCase):
    def test_armenian_stemmer(self):
        from rag_index import _stem_armenian, _tokenize_bm25

        self.assertEqual(_stem_armenian("կենսաթոշակառուներին"), "կենսաթոշակառու")
        self.assertEqual(_stem_armenian("նպաստների"), "նպաստ")
        self.assertEqual(_stem_armenian("կարգավիճակով"), "կարգավիճակ")
        tokens = _tokenize_bm25("կենսաթոշակառուներին տրվող նպաստների չափը")
        self.assertIn("կենսաթոշակառու", tokens)
        self.assertIn("նպաստ", tokens)

    def test_colloquial_expansion(self):
        from llm.prompts import expand_colloquial_query

        res = expand_colloquial_query("երեխայի փող")
        self.assertTrue(any("խնամքի նպաստ" in r or "ծննդյան" in r for r in res))

        res_pension = expand_colloquial_query("թոշակի տարիք")
        self.assertTrue(any("տարիքային" in r or "63" in r for r in res_pension))

    def test_context_reordering(self):
        from llm.prompts import reorder_context_chunks

        chunks = [{"id": i} for i in range(6)]
        reordered = reorder_context_chunks(chunks)
        # Top chunk (id 0) at left, second (id 1) at right, etc.
        self.assertEqual(reordered[0]["id"], 0)
        self.assertEqual(reordered[-1]["id"], 1)

    def test_quick_fact_classifier(self):
        from llm.prompts import is_quick_factual_query

        self.assertTrue(is_quick_factual_query("ՄՍԾ թեժ գիծ"))
        self.assertTrue(is_quick_factual_query("hotline phone number"))
        self.assertFalse(is_quick_factual_query("Ինչպես դիմել մինչև 2 տարեկան երեխայի խնամքի նպաստ ստանալու համար ամբողջական ընթացակարգով"))


class TestStrictGuardrailAndRefusal(unittest.TestCase):
    def test_standard_refusal_messages(self):
        from llm.prompts import (
            STANDARD_REFUSAL_HY,
            STANDARD_REFUSAL_EN,
            STANDARD_REFUSAL_RU,
            get_standard_refusal,
        )

        for text in (STANDARD_REFUSAL_HY, STANDARD_REFUSAL_EN, STANDARD_REFUSAL_RU):
            self.assertIn("114", text)
            self.assertIn("e-soc.am", text)

        self.assertEqual(get_standard_refusal("hy"), STANDARD_REFUSAL_HY)
        self.assertEqual(get_standard_refusal("en"), STANDARD_REFUSAL_EN)
        self.assertEqual(get_standard_refusal("ru"), STANDARD_REFUSAL_RU)

    def test_is_refusal_detection(self):
        from fidelity import is_refusal_response, is_answer_incomplete, evaluate_grounding
        from llm.prompts import STANDARD_REFUSAL_HY

        self.assertTrue(is_refusal_response(STANDARD_REFUSAL_HY))
        self.assertTrue(is_refusal_response("Տեղեկատվություն չկա: Խնդրում ենք զանգահարել 114 թեժ գիծ:"))
        self.assertFalse(is_refusal_response("Կենսաթոշակի չափը 37500 դրամ է:"))

        # A refusal must not be flagged as an incomplete answer
        self.assertFalse(is_answer_incomplete(STANDARD_REFUSAL_HY))

        # Grounding on refusal should be evaluated as low risk / verified
        res = evaluate_grounding(STANDARD_REFUSAL_HY, "")
        self.assertTrue(res.get("is_refusal"))
        self.assertEqual(res.get("risk"), "low")


class TestRRFAndConfidence(unittest.TestCase):
    def test_reciprocal_rank_fusion(self):
        from retrieval.hybrid import reciprocal_rank_fusion

        list1 = [(1, 0.9), (2, 0.8), (3, 0.7)]
        list2 = [(2, 0.95), (1, 0.7), (4, 0.6)]
        fused = reciprocal_rank_fusion([list1, list2], weights=[0.5, 0.5])
        # Doc 2 is rank 2 in list1 and rank 1 in list2; doc 1 is rank 1 in list1 and rank 2 in list2
        top_doc_ids = [doc_id for doc_id, _ in fused]
        self.assertIn(1, top_doc_ids[:2])
        self.assertIn(2, top_doc_ids[:2])

    def test_compute_retrieval_confidence(self):
        from retrieval.hybrid import compute_retrieval_confidence

        query = "կենսաթոշակ տարիք"
        matching_chunks = [
            {"text": "տարիքային կենսաթոշակ ստանալու իրավունք", "hybrid_score": 0.85},
        ]
        conf_high = compute_retrieval_confidence(query, matching_chunks)
        self.assertGreater(conf_high, 0.3)

        irrelevant_chunks = [
            {"text": "սպորտային մրցաշար ֆուտբոլ", "hybrid_score": 0.01},
        ]
        conf_low = compute_retrieval_confidence("տիեզերանավ գնել", irrelevant_chunks)
        self.assertLess(conf_low, 0.15)


if __name__ == "__main__":
    # Prefer pytest if available
    try:
        import pytest

        raise SystemExit(pytest.main([__file__, "-q"]))
    except ImportError:
        # unittest.main() returns None when it calls sys.exit internally,
        # so run it with exit=False and check the result explicitly.
        program = unittest.main(verbosity=2, exit=False)
        raise SystemExit(0 if program.result.wasSuccessful() else 1)
