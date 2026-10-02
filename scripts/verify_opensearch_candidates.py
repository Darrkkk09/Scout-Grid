"""
ScoutGrid Phase 4 Step 2 — OpenSearch Candidate Index Verification Script

Verifies:
A. Index exists ('candidates')
B. Document count
C. Mapping summary
D. Retrieves and formats one sample indexed candidate
E. Runs a simple verification term query (e.g. location = Bangalore)

Usage:
    python scripts/verify_opensearch_candidates.py
"""

import json
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

from app.services.opensearch_client import create_opensearch_client
from app.services.opensearch_index import CANDIDATES_INDEX_NAME, check_index_exists


def main() -> None:
    print("Connecting to OpenSearch for verification...")
    client = create_opensearch_client()

    # A. Index Existence Check
    exists = check_index_exists(client, CANDIDATES_INDEX_NAME)
    print(f"\nA. Index Status:")
    print(f"   Index '{CANDIDATES_INDEX_NAME}' exists: {exists}")
    if not exists:
        print("Error: Index does not exist. Run scripts/create_opensearch_index.py first.")
        sys.exit(1)

    # B. Document Count
    count_response = client.count(index=CANDIDATES_INDEX_NAME)
    doc_count = count_response.get("count", 0)
    print(f"\nB. Document Count:")
    print(f"   Indexed candidates count: {doc_count}")

    # C. Mapping Summary
    mapping_response = client.indices.get_mapping(index=CANDIDATES_INDEX_NAME)
    properties = (
        mapping_response.get(CANDIDATES_INDEX_NAME, {})
        .get("mappings", {})
        .get("properties", {})
    )
    print(f"\nC. Mapping Summary ({len(properties)} properties mapped):")
    for field, spec in properties.items():
        field_type = spec.get("type", "object")
        print(f"   - {field}: {field_type}")

    # D. Retrieve One Document
    search_one = client.search(index=CANDIDATES_INDEX_NAME, body={"query": {"match_all": {}}, "size": 1})
    hits = search_one.get("hits", {}).get("hits", [])
    print(f"\nD. Sample Document Retrieval:")
    if hits:
        sample_doc = hits[0].get("_source", {})
        print(f"   Candidate ID:     {sample_doc.get('candidate_id')}")
        print(f"   Name:             {sample_doc.get('name')}")
        print(f"   Location:         {sample_doc.get('location')}")
        print(f"   Experience Years: {sample_doc.get('experience_years')}")
        print(f"   Skills:           {sample_doc.get('skills')}")
        print(f"   Education:        {sample_doc.get('education')}")
        print(f"   Experience Count: {len(sample_doc.get('experience', []))}")
    else:
        print("   No documents found in index.")

    # E. Basic Search/Filter Query (location = Bangalore)
    test_location = "Bangalore"
    term_query = {
        "query": {
            "term": {
                "location": test_location
            }
        }
    }
    search_res = client.search(index=CANDIDATES_INDEX_NAME, body=term_query)
    match_count = search_res.get("hits", {}).get("total", {}).get("value", 0)
    print(f"\nE. Basic Filter Verification Query (location = '{test_location}'):")
    print(f"   Search successful: True")
    print(f"   Matches found:     {match_count}")

    print("\nVerification completed successfully!")


if __name__ == "__main__":
    main()
