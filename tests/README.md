# Test guide

The tests are organised by assessment part. Run the commands from the repository root after activating the virtual environment.

## File organisation

```text
tests/
  README.md
  conftest.py                 Shared local HTTP server and --live option
  part2/test_scraper.py       Extraction and summarisation
  part3/test_agent.py         Document answers, memory and calculator
  shared/test_common.py       Gemini error reporting
  live/test_gemini.py         Actual Gemini evaluations
  fixtures/                  Static HTML, JavaScript and error examples
```

`pytest.ini` configures test discovery and the live marker. `requirements-dev.txt` installs the application and development dependencies. No API key is needed for the offline suite. Chromium is needed for the browser cases.

## Run the tests

```powershell
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python -m pytest -q
```

Run one group:

```powershell
python -m pytest tests/part2 -q
python -m pytest tests/part3 -q
python -m pytest tests/shared -q
```

Run actual Gemini evaluations with the key in the local `.env` file:

```powershell
python -m pytest tests/live --live -q
```

Live tests are skipped by default. They use Gemini quota and may fail if the provider is unavailable or a rate limit is reached. Keep the API key private.

## Cases and expected outcomes

| Group | Cases | Expected outcome |
| --- | --- | --- |
| [Part 2](part2/test_scraper.py) | Article and table extraction; navigation and hidden elements | Keep article facts and remove unrelated or hidden content. |
| Part 2 | Static HTTP page, JavaScript article and loading shell | Extract the static article; render the JavaScript article; reject an unreadable loading shell. |
| Part 2 | Long articles, repeated summarisation and oversized input | Process every accepted section, keep each model input within its size limit and reject oversized sources before model calls. |
| Part 2 | Overlong or empty model output | Keep summaries within 120 words; report empty output clearly. |
| Part 2 | Invalid URL, non-HTML content, HTTP 404, timeout and oversized download | Reject unsuitable input, report errors clearly and close the connection. |
| [Part 3](part3/test_agent.py) | Valid, missing or fabricated document evidence | Accept a matching source; withhold answers without valid evidence. |
| Part 3 | Name context, reset and 12-turn memory limit | Send recent completed context to the model; clear it on reset; remove older turns. |
| Part 3 | Calculator selection, invalid expressions and tool budget | Execute supported arithmetic, return tool errors and enforce the call limit. |
| Part 3 | Malformed output or API timeout | Report the failure, preserve earlier completed context and exclude failed turns. |
| Part 3 | Incorrect numbers in model answers, incorrect answer labels and later calculation failures | Display actual tool results; reject an incorrect label or an earlier result used after a later failure. |
| Part 3 | Invented personal quotes, assistant-only evidence, name changes, varied wording and reset | Render verified user excerpts without a required prefix; reject missing evidence and reset context. |
| [Shared](shared/test_common.py) | Gemini HTTP 403, 429, 503 and 504; retry configuration | Show status-specific guidance without exposing provider response secrets or user prompts; exclude 429 from automatic retries. |
| [Live Gemini](live/test_gemini.py) | Document facts, unknown answers, name recall/reset, calculator use, ordinary refund questions, policy injection and summaries | Confirm the expected behaviour with actual model responses. |

Offline agent and summary tests replace Gemini responses with simulated responses at the point where the application calls the SDK. They check the code's behaviour, but cannot show whether a real model consistently chooses the right tool or understands its sources. Tests for downloading and rendering pages use local sample files and real Chromium. Part 1 is a proposed design and is not covered by executable tests.

## Verification status

Following the calculator and memory improvements, the offline suite passed **64 cases** and skipped **eight live cases** on 9 October 2026. See [the verification record](../docs/test-cases.md) for the run details. These results do not measure production performance or capacity with multiple users.

Earlier live runs passed four different cases using a previous version of the code. The latest memory/reset and calculator tests both stopped on HTTP 429. The updated short and long summary tests have not been run. Earlier successes do not establish that the current live suite passes.

To save a local report, add `--junitxml=tmp/test-results/offline.xml` to the offline command. Reports under `tmp/` are ignored by Git.
