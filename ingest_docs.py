#!/usr/bin/env python3
"""
ingest_docs.py

Run this script once to load all documents in ./documents into the vector store.

Usage:
    python ingest_docs.py

Add or replace files in ./documents/ and re-run to update the knowledge base.
Existing chunks are upserted (not duplicated) so it's safe to re-run.
"""

from rag.ingest import ingest_directory

if __name__ == "__main__":
    ingest_directory()
