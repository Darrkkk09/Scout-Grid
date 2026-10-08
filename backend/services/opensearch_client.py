import os
import logging
from typing import Optional
from dotenv import load_dotenv
from opensearchpy import OpenSearch

logger = logging.getLogger(__name__)

# Ensure environment variables are loaded (checks root .env and backend/.env)
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

_opensearch_client: Optional[OpenSearch] = None


def create_opensearch_client() -> OpenSearch:
    """
    Constructs and returns an OpenSearch client configured for Aiven OpenSearch using
    OPENSEARCH_HOST / OPENSEARCH_PORT / OPENSEARCH_USERNAME / OPENSEARCH_PASSWORD or OPENSEARCH_SERVICE_URI.
    Enforces TLS/SSL verification as required by hosted Aiven OpenSearch.
    """
    service_uri = os.getenv("OPENSEARCH_SERVICE_URI")
    host = os.getenv("OPENSEARCH_HOST")
    port_str = os.getenv("OPENSEARCH_PORT", "22764")
    username = os.getenv("OPENSEARCH_USERNAME")
    password = os.getenv("OPENSEARCH_PASSWORD")

    if service_uri:
        client = OpenSearch(
            hosts=[service_uri],
            verify_certs=True,
            ssl_show_warn=True,
            timeout=10,
            max_retries=3,
            retry_on_timeout=True,
        )
    elif host and username and password:
        port = int(port_str) if port_str.isdigit() else 22764
        client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=(username, password),
            use_ssl=True,
            verify_certs=True,
            ssl_show_warn=True,
            timeout=10,
            max_retries=3,
            retry_on_timeout=True,
        )
    else:
        raise ValueError(
            "Missing OpenSearch credentials. Ensure OPENSEARCH_HOST, OPENSEARCH_USERNAME, "
            "and OPENSEARCH_PASSWORD (or OPENSEARCH_SERVICE_URI) are set in .env."
        )

    return client


def get_opensearch_client() -> OpenSearch:
    """Returns a singleton OpenSearch client instance."""
    global _opensearch_client
    if _opensearch_client is None:
        _opensearch_client = create_opensearch_client()
    return _opensearch_client
