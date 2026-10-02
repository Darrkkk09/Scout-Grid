"""
ScoutGrid Phase 4 Step 1 — OpenSearch Connection Verification Script

Verifies connectivity between ScoutGrid and hosted Aiven OpenSearch.
Does NOT print credentials or sensitive tokens.

Usage:
    python scripts/test_opensearch.py
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

# Load env variables from root .env or backend/.env
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

from app.services.opensearch_client import create_opensearch_client


def main() -> None:
    print("Testing connection to Aiven OpenSearch...")

    host = os.getenv("OPENSEARCH_HOST", "not set")
    port = os.getenv("OPENSEARCH_PORT", "not set")
    print(f"Target OpenSearch Host: {host}:{port}")

    try:
        client = create_opensearch_client()
        info = client.info()

        cluster_name = info.get("cluster_name", "unknown")
        version_info = info.get("version", {})
        number = version_info.get("number", "unknown")
        distribution = version_info.get("distribution", "opensearch")

        print("\nOpenSearch connection successful")
        print(f"Cluster: {cluster_name}")
        print(f"Distribution: {distribution}")
        print(f"Version: {number}")

    except Exception as err:
        print("\nOpenSearch connection failed!")
        # Print error type and clean string without exposing password credentials
        err_msg = str(err)
        # Sanitise potential auth info if present
        if "@" in err_msg:
            err_msg = err_msg.split("@")[-1]
        print(f"Error details: {type(err).__name__} - {err_msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
