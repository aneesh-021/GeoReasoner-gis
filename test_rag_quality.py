
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Constants
INDEX_PATH = "vector_db/rag_faiss.index"
META_PATH = "vector_db/rag_metadata.json"
CHUNKS_PATH = "vector_db/cleaned_chunks.jsonl"

print("🔍 Testing RAG Retrieval Quality...")
index = faiss.read_index(INDEX_PATH)
with open(META_PATH) as f:
    ids = json.load(f)

with open(CHUNKS_PATH) as f:
    chunks = [json.loads(line) for line in f if line.strip()]
id_to_chunk = {c["tool"]: c for c in chunks}

embed_model = SentenceTransformer('all-MiniLM-L6-v2')

# Conceptual/Chat RAG Queries (Integrated Libs)
queries = [
    "How does the spatial join using 'sjoin' work in Geopandas and what predicates are supported?",
    "What is the difference between 'intersection' and 'overlay' operations for vector data?",
    "Explain how to handle Coordinate Reference Systems (CRS) transformations in Geopandas."
]

print(f"Testing {len(queries)} Queries...\n")

for q_idx, query in enumerate(queries):
    print(f"--- Query {q_idx+1}: {query} ---")
    
    # Retrieval
    q_vec = embed_model.encode([query])
    D, I = index.search(np.array(q_vec).astype('float32'), k=5)
    candidates = [ids[i] for i in I[0]]

    print("Top 5 Retrieved Tools:")
    for i, tool in enumerate(candidates):
        chunk = id_to_chunk.get(tool, {})
        print(f"  {i+1}. {tool} [{chunk.get('domain')}] - {chunk.get('description')}")
    print("\n")
