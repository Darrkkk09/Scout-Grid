"""
ScoutGrid Phase 4 Step 2 — Safe OpenSearch Index Creation Script

Connects using the existing OpenSearch client and safely creates the 'candidates'
index with mapping if it does not already exist. Never drops or recreates existing indices.

Usage:
    python scripts/create_opensearch_index.py
"""

import os
import sys

# Ensure backend directory is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

from services.opensearch_client import create_opensearch_client
from services.opensearch_index import (
    CANDIDATES_INDEX_NAME,
    check_index_exists,
    create_candidate_index,
)


def main() -> None:
    print("Connecting to OpenSearch...")
    client = create_opensearch_client()
    print(f"Index: {CANDIDATES_INDEX_NAME}\n")

    exists = check_index_exists(client, CANDIDATES_INDEX_NAME)

    if exists:
        print(f"Index '{CANDIDATES_INDEX_NAME}' already exists.")
        print("No changes made.")
    else:
        print(f"Index '{CANDIDATES_INDEX_NAME}' does not exist.")
        print("Creating index...")
        created = create_candidate_index(client, CANDIDATES_INDEX_NAME)
        if created:
            print(f"Index '{CANDIDATES_INDEX_NAME}' created successfully.")
        else:
            print(f"Failed to create index '{CANDIDATES_INDEX_NAME}'.")


if __name__ == "__main__":
    main()
