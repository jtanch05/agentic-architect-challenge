# Agentic Architect Challenge

This Developer Intern assessment uses Python and Gemini. It contains a customer-support email system design, a website scraper and summariser, and a document question-answering agent. The agent remembers recent conversation context and uses a calculator only when a question needs one.

## Deliverables

| Part | Deliverable |
| --- | --- |
| 1 | [Email system design](part1/design.md) and [architecture diagram](part1/system-design.png): email categories, escalation before drafting, approved knowledge sources, refund-policy safeguards, trade-offs and failure handling. This is a design proposal, not a working email service. |
| 2 | [Scraping script and explanation](part2/README.md): complex-page extraction, long-article processing and a 120-word summary limit. |
| 3 | [Document agent and demonstration](part3/README.md): a [sample document](part3/sample_document.md), conversation memory and a calculator selected by Gemini when needed. |
| Architecture | [One-page architecture PDF](docs/architecture.pdf): system architecture, design trade-offs and possible failure points. |

The employer did not provide a knowledge base or refund policy. The OrbitDesk handbook is fictional and is only used to demonstrate Part 3.

## Local setup

Python 3.11 or later is required; development used Python 3.13 on Windows.

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
Copy-Item .env.example .env
```

Copy `.env.example` only if `.env` does not already contain settings. Set `GEMINI_API_KEY` in `.env` to your [Google AI Studio API key](https://aistudio.google.com/apikey). `GEMINI_MODEL` selects the Gemini model; the default is `gemini-3.8-flash`. Choose a function-calling model available to your account. Live requests use your Gemini quota.

For the commands below, activate the environment with `.\.venv\Scripts\Activate.ps1` or replace `python` with `.\.venv\Scripts\python.exe`. The latter works when PowerShell blocks activation.

On macOS/Linux, use `python3 -m venv .venv`, `source .venv/bin/activate`, `python -m pip install -r requirements.txt`, `python -m playwright install chromium`, and `cp .env.example .env`.

## Run

```powershell
python -m part3.agent
python -m part2.scraper https://example.com
```

Replace the example URL with a page you are allowed to scrape. Add `--render` for a JavaScript page. To summarise a local HTML file, run `python -m part2.scraper --html PATH_TO_FILE`.

Part 3 commands: `/reset` clears session memory and `/quit` exits. Its README includes a sequence of questions that demonstrates document answers, memory and tool selection.

## Tests

Install the development dependencies and Chromium, then run the offline suite:

```powershell
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python -m pytest -q
```

Tests are grouped by Part 2, Part 3, shared provider handling and live Gemini evaluation. See the [test guide](tests/README.md) for the cases, expected outcomes and commands for each group. Offline model responses are simulated; HTTP and browser cases use a local server and real Chromium.

Live tests are skipped unless explicitly enabled. To run them with a local API key:

```powershell
python -m pytest tests/live --live -q
```

Live tests consume Gemini quota. Offline results do not establish real-model accuracy.

## Logging and limitations

Part 2 logs show processing steps, model response times, chunk counts and summary-length checks. Part 3 normally shows a waiting spinner, answers and tools used; add `--verbose` for application events on standard error. Application events omit API keys, document text and user prompts. Requests run one at a time. A simulated slow-provider check verifies sequential recovery and bounded memory; real throughput and concurrent load have not been measured.

HTTP 429 quota/rate-limit errors are reported without an automatic retry. Selected transient HTTP failures allow at most two attempts, each with a 30-second timeout. Error messages distinguish quota limits, permissions and provider timeouts.

- Part 1 is a proposed email system. Its safety checks would need to be implemented and tested in a real service.
- Part 2 handles ordinary public HTML and can render JavaScript pages within time and size limits. It does not support login pages, paywalls, CAPTCHA, infinite scrolling or every site layout.
- Part 3 sends one short document to the model and remembers the latest 12 completed turns. A matching source quote does not prove that the answer is interpreted correctly, so human review is still needed.
- The summary length, sample policy and contact-counting rules are design choices for this assessment. The employer did not provide them.

## AI assistance

Codex assisted with interpreting the assessment, drafting the design, writing code and documentation, and preparing the architecture PDF. This is AI-assisted work. The candidate should review and be able to explain every part before submitting it.
