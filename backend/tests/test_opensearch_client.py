import os
import pytest
from unittest.mock import MagicMock, patch

from app.services.opensearch_client import create_opensearch_client, get_opensearch_client


def test_create_opensearch_client_from_env(monkeypatch):
    """Verify OpenSearch client is constructed with host, auth, and TLS settings from env."""
    monkeypatch.setenv("OPENSEARCH_HOST", "mock-opensearch.example.com")
    monkeypatch.setenv("OPENSEARCH_PORT", "9200")
    monkeypatch.setenv("OPENSEARCH_USERNAME", "admin")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "secret_pass")
    monkeypatch.delenv("OPENSEARCH_SERVICE_URI", raising=False)

    with patch("app.services.opensearch_client.OpenSearch") as MockOpenSearch:
        client_mock = MagicMock()
        MockOpenSearch.return_value = client_mock

        client = create_opensearch_client()

        MockOpenSearch.assert_called_once()
        _, kwargs = MockOpenSearch.call_args
        assert kwargs["hosts"] == [{"host": "mock-opensearch.example.com", "port": 9200}]
        assert kwargs["http_auth"] == ("admin", "secret_pass")
        assert kwargs["use_ssl"] is True
        assert kwargs["verify_certs"] is True


def test_create_opensearch_client_from_service_uri(monkeypatch):
    """Verify OpenSearch client supports OPENSEARCH_SERVICE_URI configuration."""
    monkeypatch.setenv("OPENSEARCH_SERVICE_URI", "https://admin:pass@mock-host:22764")

    with patch("app.services.opensearch_client.OpenSearch") as MockOpenSearch:
        create_opensearch_client()
        MockOpenSearch.assert_called_once()
        _, kwargs = MockOpenSearch.call_args
        assert kwargs["hosts"] == ["https://admin:pass@mock-host:22764"]
        assert kwargs["verify_certs"] is True


def test_create_opensearch_client_missing_credentials(monkeypatch):
    """Verify ValueError is raised if OpenSearch environment variables are missing."""
    monkeypatch.delenv("OPENSEARCH_HOST", raising=False)
    monkeypatch.delenv("OPENSEARCH_SERVICE_URI", raising=False)
    monkeypatch.delenv("OPENSEARCH_USERNAME", raising=False)
    monkeypatch.delenv("OPENSEARCH_PASSWORD", raising=False)

    with pytest.raises(ValueError) as exc_info:
        create_opensearch_client()

    assert "Missing OpenSearch credentials" in str(exc_info.value)
