"""
rag/ingest.py

Loads documents from the ./documents folder, splits them into chunks,
embeds each chunk with Google text-embedding-004, and stores them in ChromaDB.

Run this once when you add or update documents:
    python -m rag.ingest
"""

import os
import uuid
import hashlib
from pathlib import Path

import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
DOCUMENTS_DIR  = Path("./documents")
CHROMA_PATH    = "./chroma_db"
COLLECTION_NAME = "documents"
CHUNK_SIZE     = 800    # characters per chunk
CHUNK_OVERLAP  = 120    # overlap between consecutive chunks

# ── Clients ───────────────────────────────────────────────────────────────────
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise EnvironmentError("GOOGLE_API_KEY not set. Check your .env file.")

genai.configure(api_key=api_key)

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)


# ── Text extraction ───────────────────────────────────────────────────────────
def extract_text(file_path: Path) -> str:
    """Extract raw text from .txt, .md, or .pdf files."""
    suffix = file_path.suffix.lower()

    if suffix in (".txt", ".md"):
        return file_path.read_text(encoding="utf-8", errors="ignore")

    elif suffix == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        except ImportError:
            print("  ⚠  pypdf not installed — skipping PDF. Run: pip install pypdf")
            return ""

    else:
        print(f"  ⚠  Unsupported file type: {suffix} — skipping {file_path.name}")
        return ""


# ── Text splitting ────────────────────────────────────────────────────────────
def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks on sentence/paragraph boundaries."""
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            # Try to break at a sentence or paragraph boundary
            for boundary in ["\n\n", "\n", ". ", " "]:
                idx = text.rfind(boundary, start, end)
                if idx > start:
                    end = idx + len(boundary)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


# ── Embedding ─────────────────────────────────────────────────────────────────
def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Embed a list of text chunks using Google text-embedding-004."""
    embeddings = []
    for i, chunk in enumerate(chunks):
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=chunk,
            task_type="retrieval_document",
        )
        embeddings.append(result["embedding"])
        if (i + 1) % 10 == 0:
            print(f"    Embedded {i + 1}/{len(chunks)} chunks...")
    return embeddings


# ── Deduplication helper ──────────────────────────────────────────────────────
def chunk_id(source: str, chunk_text: str) -> str:
    """Deterministic ID so re-ingesting the same doc doesn't create duplicates."""
    digest = hashlib.md5(f"{source}::{chunk_text}".encode()).hexdigest()
    return digest


# ── Main ingestion ────────────────────────────────────────────────────────────
def ingest_directory(docs_dir: Path = DOCUMENTS_DIR):
    if not docs_dir.exists():
        print(f"Documents directory not found: {docs_dir}")
        print("Create it and add your PDF or text files, then re-run.")
        return

    files = [
        f for f in docs_dir.iterdir()
        if f.is_file() and f.suffix.lower() in (".txt", ".md", ".pdf")
    ]

    if not files:
        print(f"No supported files found in {docs_dir}/")
        print("Supported formats: .txt  .md  .pdf")
        return

    total_chunks = 0

    for file_path in sorted(files):
        print(f"\n📄 Processing: {file_path.name}")

        text = extract_text(file_path)
        if not text.strip():
            print("   (empty or unreadable — skipped)")
            continue

        chunks = split_text(text)
        print(f"   Split into {len(chunks)} chunks")

        if not chunks:
            continue

        print(f"   Embedding {len(chunks)} chunks...")
        embeddings = embed_chunks(chunks)

        # Build ChromaDB upsert payload
        ids       = [chunk_id(file_path.name, c) for c in chunks]
        metadatas = [{"source": file_path.name, "chunk_index": i} for i in range(len(chunks))]

        collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        total_chunks += len(chunks)
        print(f"   ✓ Stored {len(chunks)} chunks")

    print(f"\n✅ Ingestion complete. Total chunks in store: {collection.count()}")


if __name__ == "__main__":
    print("=" * 52)
    print("  RAG Document Ingestion")
    print("=" * 52)
    ingest_directory()
