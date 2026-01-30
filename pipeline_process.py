"""
pipeline_process.py

Phase 3: Cleaning & Standardization

Responsibilities:
- Read raw geospatial snapshots
- Perform validation and normalization
- Output analytics-ready processed data

IMPORTANT:
- Does NOT modify raw data
- Does NOT create embeddings
- Does NOT build indexes
"""

import json
from pathlib import Path
from datetime import datetime


# ===============================
# Configuration
# ===============================

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")


# ===============================
# Helper Functions
# ===============================

def get_latest_raw_snapshot():
    """
    Returns the most recent raw snapshot directory.
    """
    snapshots = sorted([p for p in RAW_DATA_DIR.iterdir() if p.is_dir()])
    if not snapshots:
        raise RuntimeError("No raw snapshots found.")
    return snapshots[-1]


def load_raw_data(snapshot_dir):
    """
    Loads raw geospatial data.
    """
    data_file = snapshot_dir / "source_data.json"
    if not data_file.exists():
        raise FileNotFoundError(f"Missing source data in {snapshot_dir}")
    with open(data_file) as f:
        return json.load(f)


def validate_raw_data(data):
    """
    Basic validation checks.
    """
    if "features" not in data:
        raise ValueError("Raw data missing 'features' key.")
    return True


def standardize_data(data):
    """
    Placeholder for cleaning & standardization logic.

    Future responsibilities:
    - CRS normalization
    - Geometry validation
    - Schema consistency
    """
    # Currently pass-through
    return data


def save_processed_data(date_str, data):
    """
    Saves processed data to data/processed/.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_file = PROCESSED_DATA_DIR / f"{date_str}.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    return output_file


# ===============================
# Main Processing Flow
# ===============================

def run_processing():
    print(" Starting geospatial data processing...")

    snapshot_dir = get_latest_raw_snapshot()
    date_str = snapshot_dir.name
    print(f" Using raw snapshot: {snapshot_dir}")

    raw_data = load_raw_data(snapshot_dir)
    validate_raw_data(raw_data)

    processed_data = standardize_data(raw_data)
    output_file = save_processed_data(date_str, processed_data)

    print(f" Processed data saved to: {output_file}")


if __name__ == "__main__":
    run_processing()