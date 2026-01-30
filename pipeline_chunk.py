"""
pipeline_chunk.py

Phase 4: Analytical Chunk Generation

Responsibilities:
- Read processed geospatial datasets
- Convert them into LLM-ready analytical chunks
- Write chunks to data/analytical/

IMPORTANT:
- No embeddings
- No indexing
- No changes to existing RAG logic
"""

import json
from pathlib import Path


RAW_PROCESSED_DIR = Path("data/processed")
ANALYTICAL_DIR = Path("data/analytical")


def get_latest_processed_file():
    processed_files = sorted(RAW_PROCESSED_DIR.glob("*.json"))
    if not processed_files:
        raise RuntimeError("No processed datasets found.")
    return processed_files[-1]


def load_processed_data(file_path):
    with open(file_path) as f:
        return json.load(f)


def generate_chunks(data, date_str):
    chunks = []

    summary_text = (
        f"Geospatial dataset snapshot from {date_str}. "
        f"Contains {len(data.get('features', []))} features. "
        f"Source: {data.get('source', 'unknown')}."
    )

    chunk = {
        "text": summary_text,
        "data_version": date_str,
        "source": data.get("source", "unknown"),
        "chunk_type": "dataset_summary"
    }

    chunks.append(chunk)
    return chunks


def save_chunks(date_str, chunks):
    ANALYTICAL_DIR.mkdir(parents=True, exist_ok=True)
    output_file = ANALYTICAL_DIR / f"{date_str}_chunks.jsonl"

    with open(output_file, "w") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk) + "\n")

    return output_file


def run_chunk_generation():
    print("Starting analytical chunk generation")

    processed_file = get_latest_processed_file()
    date_str = processed_file.stem

    print(f"Using processed dataset: {processed_file}")

    data = load_processed_data(processed_file)
    chunks = generate_chunks(data, date_str)

    output_file = save_chunks(date_str, chunks)
    print(f"Chunks written to: {output_file}")


if __name__ == "__main__":
    run_chunk_generation()