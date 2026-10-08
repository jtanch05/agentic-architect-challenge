"""Shared provider-error handling with simulated Gemini responses."""

import logging
from unittest.mock import Mock

import pytest
from google.genai import errors

from common import generate


@pytest.mark.parametrize("status", [403, 429, 503])
def test_provider_error_reports_status_without_exposing_response_details(status, caplog):
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
