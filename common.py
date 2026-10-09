"""Shared Gemini connection and logs; credentials are never logged."""

import json
import logging
import os
from pathlib import Path
from time import perf_counter

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

ROOT = Path(__file__).resolve().parent


def log_event(event, **fields):
    logging.getLogger("assessment").info(json.dumps({"event": event, **fields}))


def create_client():
    load_dotenv(ROOT / ".env")
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Set GEMINI_API_KEY in the local .env file first.")
    client = genai.Client(
        api_key=key,
        http_options=types.HttpOptions(
            timeout=30000,
            retry_options=types.HttpRetryOptions(
                attempts=2, initial_delay=1, max_delay=2,
                http_status_codes=[408, 500, 502, 503, 504],
            ),
        ),
    )
    return client, os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def generate(client, model, contents, config):
    start = perf_counter()
    try:
        result = client.models.generate_content(model=model, contents=contents, config=config)
    except errors.APIError as exc:
        log_event("model_error", status=exc.code, latency_ms=round((perf_counter() - start) * 1000))
        guidance = {
            400: "Check the request and model configuration.",
            401: "Check your API key.",
            403: "Check your API key and permission to use this model.",
            404: "Check that the configured model is available to your account.",
            408: "The request timed out. Try again later.",
            429: "Rate limit or quota reached. Check AI Studio usage; wait for the limit to reset before retrying.",
            500: "Gemini encountered a server error. Try again later.",
            502: "Gemini is temporarily unavailable. Try again later.",
            503: "Gemini is temporarily unavailable. Try again later.",
            504: "Gemini timed out while processing the request. Try again later.",
        }.get(exc.code, "Try again later or check your model configuration.")
        raise RuntimeError(f"Gemini request failed (HTTP {exc.code}). {guidance}") from None
    except httpx.HTTPError:
        log_event("model_error", status="network", latency_ms=round((perf_counter() - start) * 1000))
        raise RuntimeError("Gemini connection failed or timed out. Try again later.") from None
    log_event("model_response", latency_ms=round((perf_counter() - start) * 1000))
    return result
