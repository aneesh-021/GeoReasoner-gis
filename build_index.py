# build_index.py
# Build FAISS vector index from GIS tool chunks
# Uses improved embedding text generation for better RAG retrieval

import json
import numpy as np
import faiss
import os
from sentence_transformers import SentenceTransformer

# Import gepro utilities for better embedding text
from gepro.utils import get_embedding_text, clean_chunk, deduplicate_chunks

# === Configuration ===
DATA_PATH = "data/chunks.jsonl"
VECTOR_DB_PATH = "vector_db"
INDEX_FILE = os.path.join(VECTOR_DB_PATH, "rag_faiss.index")
META_FILE = os.path.join(VECTOR_DB_PATH, "rag_metadata.json")

print("🔍 Loading chunks from", DATA_PATH)
with open(DATA_PATH) as f:
    raw_chunks = [json.loads(line) for line in f if line.strip()]

print(f"📦 Loaded {len(raw_chunks)} raw chunks.")

# === Clean and deduplicate chunks ===
print("🧹 Cleaning chunks...")
cleaned_chunks = []
for chunk in raw_chunks:
    result = clean_chunk(chunk)
    if result:
        cleaned_chunks.append(result)

print(f"  After cleaning: {len(cleaned_chunks)} chunks")

unique_chunks = deduplicate_chunks(cleaned_chunks)
print(f"  After dedup: {len(unique_chunks)} chunks")

# === Prepare data with rich embedding text ===
texts = []
ids = []
chunks_for_save = []

for chunk in unique_chunks:
    tool = chunk.get('tool', '')
    if not tool:
        continue
    
    # Generate rich embedding text combining all fields
    embedding_text = get_embedding_text(chunk)
    texts.append(embedding_text)
    ids.append(tool)
    chunks_for_save.append(chunk)

print(f"📝 Prepared {len(texts)} chunks for embedding.")

# === Encode embeddings ===
print("⚙️ Encoding embeddings with SentenceTransformer...")
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts, show_progress_bar=True)
embeddings = np.array(embeddings).astype("float32")

# === Build FAISS index ===
print("🧠 Building FAISS index...")
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# === Save ===
os.makedirs(VECTOR_DB_PATH, exist_ok=True)
faiss.write_index(index, INDEX_FILE)

with open(META_FILE, "w") as f:
    json.dump(ids, f)

# Save cleaned chunks for reference
CLEANED_CHUNKS_FILE = os.path.join(VECTOR_DB_PATH, "cleaned_chunks.jsonl")
with open(CLEANED_CHUNKS_FILE, "w") as f:
    for chunk in chunks_for_save:
        f.write(json.dumps(chunk) + "\n")

print(f"\n✅ FAISS index saved to: {INDEX_FILE}")
print(f"✅ Metadata saved to: {META_FILE}")
print(f"✅ Cleaned chunks saved to: {CLEANED_CHUNKS_FILE}")
print(f"\n📊 Stats:")
print(f"   Original chunks: {len(raw_chunks)}")
print(f"   Indexed chunks: {len(texts)}")
print(f"   Embedding dimension: {embeddings.shape[1]}")
