# Test guide

The tests are grouped by the part of the assessment they check. Run commands from the repository root after activating the virtual environment.

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

Live cases are skipped by default. They consume quota and can fail because of provider availability or rate limits. Keep the API key private.

## Cases and expected outcomes

| Group | Cases | Expected outcome |
| --- | --- | --- |
| [Part 2](part2/test_scraper.py) | Article and table extraction; navigation and hidden elements | Keep article facts and remove unrelated or hidden content. |
| Part 2 | Static HTTP page, JavaScript article and loading shell | Extract the static article; render the JavaScript article; reject an unreadable loading shell. |
| Part 2 | Long input, repeated reduction and over-budget input | Process every accepted source section, bound each content input and reject oversized sources before model calls. |
| Part 2 | Overlong or empty model output | Keep summaries within 120 words; report empty output clearly. |
| Part 2 | Invalid URL, non-HTML content, HTTP 404, timeout and oversized download | Reject unsuitable input, report errors clearly and close the connection. |
| [Part 3](part3/test_agent.py) | Valid, missing or fabricated document evidence | Accept a matching source; withhold answers without valid evidence. |
| Part 3 | Name context, reset and 12-turn memory limit | Send recent completed context to the model; clear it on reset; remove older turns. |
| Part 3 | Calculator selection, invalid expressions and tool budget | Execute supported arithmetic, return tool errors and enforce the call limit. |
| Part 3 | Malformed output or API timeout | Report the failure, preserve earlier completed context and exclude failed turns. |
| [Shared](shared/test_common.py) | Gemini HTTP 403, 429 and 503 | Show the status without exposing provider response secrets or user prompts. |
| [Live Gemini](live/test_gemini.py) | Document facts, unknown answers, name recall/reset, calculator use, ordinary refund questions, policy injection and summaries | Confirm the expected behaviour with actual model responses. |

Offline agent and summary tests simulate Gemini at the SDK boundary. They check application behaviour, not whether a real model consistently selects the right tool or interprets evidence correctly. HTTP and browser cases use local fixtures, including real Chromium. Part 1 is a proposed design and is not exercised by this suite.

## Verification status

After this reorganisation, `python -m pytest -q` passed **46 cases** and skipped **seven live cases** in **11.82 seconds** on 9 October 2026. The same assertions and fixtures were retained. This is test-suite runtime, not a production performance benchmark.

Earlier live runs completed four distinct cases successfully. Name memory/reset, ordinary refund questions and the complete long-summary case remain unverified after provider HTTP 429/503 errors. Those historical results are not a pass for the complete live suite.

To save a local report, add `--junitxml=tmp/test-results/offline.xml` to the offline command. Reports under `tmp/` are ignored by Git.
