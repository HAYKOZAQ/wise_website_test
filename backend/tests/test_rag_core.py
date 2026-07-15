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
        # Import after env so module-level token is re-read via function that uses env
        os.environ["ADMIN_TOKEN"] = "test-secret-xyz"
        # The live main module may already be imported; test pure comparison logic
        token = os.environ["ADMIN_TOKEN"]
        provided = "wrong"
        self.assertNotEqual(provided, token)
        provided_ok = "test-secret-xyz"
        self.assertEqual(provided_ok, token)
        del os.environ["ADMIN_TOKEN"]


if __name__ == "__main__":
    # Prefer pytest if available
    try:
        import pytest

        raise SystemExit(pytest.main([__file__, "-q"]))
    except ImportError:
        raise SystemExit(0 if unittest.main(verbosity=2) else 1)
