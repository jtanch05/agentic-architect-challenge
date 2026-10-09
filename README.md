# Agentic Architect Challenge

This project uses Python and Gemini to address the three parts of the Developer Intern assessment. It includes a design for processing customer-support emails, a website scraper that produces concise summaries, and an agent that answers questions from a document. The agent remembers recent conversation context and can choose to use a calculator when needed.

## Deliverables

| Part | Deliverable |
| --- | --- |
| 1 | [Email system design](part1/design.md) and [architecture diagram](part1/system-design.png): email categories, escalation before drafting, approved knowledge sources, refund-policy safeguards, trade-offs and failure handling. This is a design proposal, not a working email service. |
| 2 | [Scraping script and explanation](part2/README.md): complex-page extraction, long-article processing and a 120-word summary limit. |
| 3 | [Document agent and demonstration](part3/README.md): a [sample document](part3/sample_document.md), conversation memory and a calculator selected by Gemini when needed. |
| Architecture | [One-page architecture PDF](docs/architecture.pdf): system architecture, design trade-offs and possible failure points. |

The employer did not provide a knowledge base or refund policy. The ClearDesk handbook is fictional and is only used to demonstrate Part 3.

## Local setup

Python 3.11 or later is required. The project was developed using Python 3.13 on Windows.

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
Copy-Item .env.example .env
```

Skip the copy command if `.env` already contains your settings. Set `GEMINI_API_KEY` in `.env` to your [Google AI Studio API key](https://aistudio.google.com/apikey). Use `GEMINI_MODEL` to select a model that supports function calling and is available to your account. The default is `gemini-3.8-flash`. Requests to Gemini count towards your API quota.

On macOS/Linux, use `python3 -m venv .venv`, `source .venv/bin/activate`, `python -m pip install -r requirements.txt`, `python -m playwright install chromium`, and `cp .env.example .env`.

## Run

After configuring `.env`, activate the virtual environment from the repository root. Activation makes `python` use the project's installed packages. Repeat the activation step whenever you open a new terminal session.

```powershell
.\.venv\Scripts\Activate.ps1
python -m part3.agent
python -m part2.scraper https://example.com
```

If PowerShell blocks activation, run the project's Python executable directly:

```powershell
.\.venv\Scripts\python.exe -m part3.agent
.\.venv\Scripts\python.exe -m part2.scraper https://example.com
```

This alternative does not require activation. For other commands in this guide, replace `python` with `.\.venv\Scripts\python.exe` if the environment is not activated.

Replace the example URL with a page you are allowed to scrape. Add `--render` for a JavaScript page. To summarise a local HTML file, run `python -m part2.scraper --html PATH_TO_FILE`.

Part 3 commands: `/reset` clears session memory; `/quit` or `/exit` exits. Its README includes a sequence of questions that demonstrates document answers, memory and tool selection.

## Tests

Install the development dependencies and Chromium, then run the offline suite:

```powershell
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python -m pytest -q
```

The tests are organised into Part 2, Part 3, shared API error handling and live Gemini evaluations. The [test guide](tests/README.md) lists the cases, expected outcomes and commands for each group. Offline tests use simulated model responses. Tests for downloading and rendering pages use a local server and real Chromium.

To run live tests with a local API key, include `--live`:

```powershell
python -m pytest tests/live --live -q
```

Live tests use Gemini quota. Passing offline tests does not show how accurately Gemini answers real questions.

Short and long articles have separate live summary tests. Run `python -m pytest tests/live --live -k short -q`, or replace `short` with `long`. These tests check whether important prices, support hours, a date and policy conditions are preserved, as well as the summary length.

## Logging and limitations

Part 2 logs record the processing steps, model response times, number of chunks and summary-length checks. Part 3 normally displays a waiting spinner, the answer and any tools used. Add `--verbose` to show diagnostic events on standard error. Application logs exclude API keys, document text and user prompts.

Requests run one at a time. A test with simulated delays checks that the agent recovers after errors and keeps its memory within the 12-turn limit. Performance with real Gemini requests or multiple users has not been measured.

In Part 2, add `--usage-log summary-usage.log` to save model-call counts to a local file. Usage information stays out of the terminal, and this option adds no usage restrictions. The count covers calls made by the application; automatic retries by the Gemini SDK can make additional HTTP requests. Anyone testing the project needs a Gemini key with available quota. A public service would also need authentication, limits on requests per user, controls on simultaneous requests and cost monitoring.

The application reports HTTP 429 errors when a rate or quota limit is reached and does not retry them automatically. Selected temporary HTTP errors allow up to two attempts, with a 30-second timeout for each attempt. Error messages explain whether the problem concerns quota, permissions or a provider timeout.

- Part 1 is a proposed email system. Its safety checks would need to be implemented and tested in a real service.
- Part 2 handles ordinary public HTML and can render JavaScript pages within time and size limits. It does not support login pages, paywalls, CAPTCHA, infinite scrolling or every site layout.
- Part 3 sends one short document to the model and remembers the latest 12 completed turns. A matching source quote does not prove that the model understood it correctly, so human review is still needed.
- The 120-word summary limit, fictional sample policy and assumptions about counting contacts are project choices. The employer specifies escalation after more than three contacts in seven days.

## AI assistance

Codex assisted with interpreting the assessment, drafting the design, writing code and documentation, and preparing the architecture PDF. This is AI-assisted work.
