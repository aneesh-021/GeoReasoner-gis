"""
pipeline_index.py

Phase 5: Versioned Vector Indexing

Responsibilities:
- Build FAISS indexes per data version
- Never overwrite existing indexes
- Maintain a latest pointer

IMPORTANT:
- Does NOT modify existing vector_db files
- Uses analytical chunks only
"""

import json
import os
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


ANALYTICAL_DIR = Path("data/analytical")
VECTOR_DB_DIR = Path("vector_db/versions")


def get_latest_chunk_file():
    chunk_files = sorted(ANALYTICAL_DIR.glob("*_chunks.jsonl"))
    if not chunk_files:
        raise RuntimeError("No analytical chunks found.")
    return chunk_files[-1]


def load_chunks(chunk_file):
    chunks = []
    with open(chunk_file) as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def build_index(chunks):
    texts = [c["text"] for c in chunks]

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts)
    embeddings = np.array(embeddings).astype("float32")

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    return index, texts


def save_versioned_index(date_str, index, chunks):
    version_dir = VECTOR_DB_DIR / date_str
    version_dir.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(version_dir / "rag_faiss.index"))

    with open(version_dir / "rag_metadata.json", "w") as f:
        json.dump([c.get("chunk_type") for c in chunks], f)

    with open(version_dir / "cleaned_chunks.jsonl", "w") as f:
        for c in chunks:
            f.write(json.dumps(c) + "\n")

    latest_file = VECTOR_DB_DIR / "latest"
    with open(latest_file, "w") as f:
        f.write(date_str)


def run_indexing():
    print("Starting versioned index build")

    chunk_file = get_latest_chunk_file()
    date_str = chunk_file.name.split("_")[0]

    print(f"Using chunks from: {chunk_file}")

    chunks = load_chunks(chunk_file)
    index, _ = build_index(chunks)

    save_versioned_index(date_str, index, chunks)

    print(f"Index built for version: {date_str}")


if __name__ == "__main__":
    run_indexing()