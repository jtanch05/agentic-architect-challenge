# Agentic Architect Challenge

Developer Intern assessment using Python and Gemini: customer-support email architecture, website scraping and summarisation, and a document agent with memory and conditional tool use.

## Deliverables

| Part | Deliverable |
| --- | --- |
| 1 | [Email system design](part1/design.md) and [architecture diagram](part1/system-design.png): classification, escalation before drafting, knowledge grounding, refund safeguards, trade-offs and failure handling. This is a proposed architecture. |
| 2 | [Scraping script and explanation](part2/README.md): complex-page extraction, long-content processing and a 120-word summary guardrail. |
| 3 | [Document agent and demonstration](part3/README.md): [sample document](part3/sample_document.md), conversation memory and Gemini-selected calculator. |
| Architecture | [One-page architecture PDF](docs/architecture.pdf) explaining the architecture, trade-offs and failure points. |

No employer knowledge base or refund policy was supplied. The OrbitDesk handbook is fictional demonstration data.

## Local setup

Python 3.11 or later is required; development used Python 3.13 on Windows.

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
Copy-Item .env.example .env
```

Copy `.env.example` only if `.env` does not already contain your settings. Set `GEMINI_API_KEY` in `.env` to your [Google AI Studio API key](https://aistudio.google.com/apikey). `GEMINI_MODEL` selects the Gemini model; the configured default is `gemini-3.8-flash`. Use a model available to your account that supports function calling. Live requests consume provider quota.

For the commands below, activate the environment with `.\.venv\Scripts\Activate.ps1` or replace `python` with `.\.venv\Scripts\python.exe`. The latter works when PowerShell blocks activation.

On macOS/Linux, use `python3 -m venv .venv`, `source .venv/bin/activate`, `python -m pip install -r requirements.txt`, `python -m playwright install chromium`, and `cp .env.example .env`.

## Run

```powershell
python -m part3.agent
python -m part2.scraper https://example.com
```

Replace the example URL with a permitted article. Add `--render` for JavaScript pages. To summarise a local HTML file, use `python -m part2.scraper --html PATH_TO_FILE`.

Part 3 commands: `/reset` clears session memory and `/quit` exits. Its README includes a multi-turn demonstration covering document answers, memory and conditional tool use.

## Operational behavior and limitations

Logs on stderr report stages, model-call latency, chunk counts, tools and guardrail outcomes. They omit keys, document bodies and user prompts. Requests run sequentially; no load benchmark or production reliability is claimed.

- Part 1 is a design, not an implemented mailbox service. Its document includes planned acceptance checks.
- Part 2 supports ordinary public HTML and bounded browser rendering. It does not handle authentication, paywalls, CAPTCHA, infinite scrolling or every site's layout.
- Part 3 uses one short document in full context and retains the latest 12 completed turns. Citation matching checks excerpts, not the truth of every interpretation; human review remains necessary.
- Summary limits, sample policies and contact-counting assumptions are documented design choices, not employer-provided facts.

## AI assistance

Codex assisted with interpreting the assessment, drafting the design, writing code and documentation, and preparing the architecture PDF. This is AI-assisted work. The candidate should understand and be able to explain every submitted component.
