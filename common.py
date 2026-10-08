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
            retry_options=types.HttpRetryOptions(attempts=2, initial_delay=1, max_delay=2),
        ),
    )
    return client, os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def generate(client, model, contents, config):
    start = perf_counter()
    try:
        result = client.models.generate_content(model=model, contents=contents, config=config)
    except errors.APIError as exc:
        log_event("model_error", status=exc.code)
        raise RuntimeError(f"Gemini request failed (HTTP {exc.code}); check key, model, and quota.") from None
    except httpx.HTTPError:
        log_event("model_error", status="network")
        raise RuntimeError("Gemini connection failed or timed out. Try again later.") from None
    log_event("model_response", latency_ms=round((perf_counter() - start) * 1000))
    return result
