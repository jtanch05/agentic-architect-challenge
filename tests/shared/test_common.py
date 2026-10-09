"""Shared provider-error handling with simulated Gemini responses."""

import logging
from unittest.mock import Mock

import pytest
from google.genai import errors

from common import generate


@pytest.mark.parametrize("status, guidance", [
    (403, "permission"), (429, "limit to reset"), (503, "temporarily unavailable"), (504, "timed out"),
])
def test_provider_error_reports_status_without_exposing_response_details(status, guidance, caplog):
    secret = "synthetic-secret-never-a-real-key"
    client = Mock()
    client.models.generate_content.side_effect = errors.APIError(
        status, {"error": {"message": f"Provider rejected key {secret}"}},
    )
    with caplog.at_level(logging.INFO, logger="assessment"):
        with pytest.raises(RuntimeError, match=f"HTTP {status}") as failure:
            generate(client, "test-model", "private prompt", None)
    assert secret not in str(failure.value) + caplog.text
    assert "private prompt" not in caplog.text
    assert "model_error" in caplog.text
    assert guidance in str(failure.value)
    assert "latency_ms" in caplog.text


def test_client_retries_transient_failures_but_not_quota_errors(monkeypatch):
    import common

    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")
    monkeypatch.setattr(common, "load_dotenv", Mock())
    factory = Mock()
    monkeypatch.setattr(common.genai, "Client", factory)
    common.create_client()
    options = factory.call_args.kwargs["http_options"]
    assert options.timeout == 30000
    assert options.retry_options.attempts == 2
    assert 429 not in options.retry_options.http_status_codes
    assert {503, 504}.issubset(options.retry_options.http_status_codes)
