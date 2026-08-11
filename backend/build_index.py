"""Build the deployable corpus and compact search index.

Usage:
    python backend/build_index.py
    python backend/build_index.py --force

Use --sparse-only for a small build machine without sentence-transformers.
An existing FAISS file is preserved during sparse-only migration when FAISS
is installed, so the Hugging Face image can still use dense query search.
"""

from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="refresh source data before indexing")
    parser.add_argument(
        "--sparse-only",
        action="store_true",
        help="skip dense embedding generation and persist compact BM25",
    )
    args = parser.parse_args()

    # These must be set before importing rag_engine because its backend choice
    # is intentionally process-wide for a consistent startup configuration.
    if args.sparse_only:
        os.environ["USE_LOCAL_EMBEDDER"] = "0"
        os.environ["USE_LOCAL_TFIDF"] = "0"

    backend = os.path.dirname(os.path.abspath(__file__))
    if backend not in sys.path:
        sys.path.insert(0, backend)

    if args.force or not os.path.exists(os.path.join(backend, "data", "mlsa_programs.json")):
        from scraper import run_scraper

        run_scraper(force_arlis=args.force, force_all=args.force)

    from rag_engine import RAGEngine

    engine = RAGEngine()
    print(
        "Index ready: "
        f"documents={engine.document_count}, chunks={len(engine.chunks)}, "
        f"backend={engine.vector_backend}, dense={engine.vector_enabled}, "
        f"hash={engine.corpus_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
