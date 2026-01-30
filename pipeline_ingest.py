"""
pipeline_ingest.py

Phase 2: Weekly Geospatial Data Ingestion

Responsibilities:
- Fetch weekly geospatial data from a GIS source
- Store raw, immutable snapshots (date-based)
- Save ingestion metadata for traceability

IMPORTANT:
- No cleaning
- No transformations
- No embeddings
- No indexing
"""

import os
import json
from datetime import datetime
from pathlib import Path


# ===============================
# Configuration
# ===============================

RAW_DATA_DIR = Path("data/raw")


# ===============================
# Helper Functions
# ===============================

def get_ingestion_date():
    """
    Returns ingestion date in YYYY-MM-DD format.
    """
    return datetime.utcnow().strftime("%Y-%m-%d")


def create_raw_snapshot_dir(date_str):
    """
    Creates a dated directory under data/raw/
    """
    snapshot_dir = RAW_DATA_DIR / date_str
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    return snapshot_dir


def fetch_geospatial_data():
    """
    Fetch geospatial data from source.

    NOTE:
    - This is intentionally a placeholder.
    - In real usage, this could be:
        - Satellite API
        - GIS library export
        - Weekly data dump
    """
    # Placeholder example
    data = {
        "source": "mock_gis_provider",
        "description": "Weekly geospatial snapshot",
        "features": []
    }
    return data


def save_raw_data(snapshot_dir, data):
    """
    Saves raw geospatial data to disk.
    """
    output_file = snapshot_dir / "source_data.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    return output_file


def save_metadata(snapshot_dir, metadata):
    """
    Saves ingestion metadata.
    """
    meta_file = snapshot_dir / "metadata.json"
    with open(meta_file, "w") as f:
        json.dump(metadata, f, indent=2)
    return meta_file


# ===============================
# Main Ingestion Flow
# ===============================

def run_ingestion():
    print("Starting weekly geospatial ingestion...")

    date_str = get_ingestion_date()
    print(f"Ingestion date: {date_str}")

    snapshot_dir = create_raw_snapshot_dir(date_str)
    print(f"Raw snapshot directory: {snapshot_dir}")

    data = fetch_geospatial_data()
    data_file = save_raw_data(snapshot_dir, data)

    metadata = {
        "ingestion_date": date_str,
        "data_file": str(data_file),
        "source": data.get("source"),
        "record_count": len(data.get("features", []))
    }

    save_metadata(snapshot_dir, metadata)

    print("Ingestion completed successfully.")


if __name__ == "__main__":
    run_ingestion()
