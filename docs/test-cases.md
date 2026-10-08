# Assessment test cases

Latest offline run: 9 October 2026. Earlier live runs: 9 October 2026. Windows, Python 3.13.1.

**Latest executed result: 46 passed, 7 skipped in 11.82 seconds.** This is suite runtime, not a production throughput measurement. Parameterised inputs count as separate pytest cases.

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml=tmp/test-results/offline.xml
```

An ignored XML report can be regenerated under `tmp/`. Tests use the real application interfaces. Gemini is simulated at its external SDK boundary; HTTP/browser cases use local fixtures, including real headless Chromium. No external website or live Gemini model was used in this run.

## Part 3: document agent (21 executed cases)

Source: [test_agent.py](../tests/part3/test_agent.py).

| ID | Scenario / input | Expected outcome | Cases | Result |
| --- | --- | --- | --- | --- |
| A01 | Ask how to contact support; model supplies a matching excerpt. | Answer includes the supported address and `[S1]`; no tool runs. | 1 | Pass |
| A02 | State a name, ask for it later, then reset. | Prior name context is available to the model; reset removes it. | 1 | Pass |
| A03 | Model selects `calculator("35 * 28")`. | Actual tool returns 980 to the model; final answer accepted and tool recorded. | 1 | Pass |
| A04 | Calculator receives `1 / 0`, a Python import/call, `2 ** 1000`, or `1e309`. | Reject each expression with a controlled error. | 4 | Pass |
| A05 | Model cites an invented 90-day refund excerpt. | Withhold the unsupported answer. | 1 | Pass |
| A06 | Model repeatedly requests calculation. | Stop at the two-tool budget; do not retain the failed turn. | 1 | Pass |
| A07 | API times out after a completed name turn. | Clear connection error; earlier completed context remains. | 1 | Pass |
| A08 | Reply is non-JSON, a JSON list, missing fields, wrongly typed sources, an unknown kind, or an empty answer; then a valid reply arrives. | Report invalid output, exclude the failed turn, and allow the next question to succeed. | 6 | Pass |
| A09 | Document answer has no sources, a nonexistent section, or a blank quote. | Withhold the answer in each case. | 3 | Pass |
| A10 | Calculator divides by zero; model then claims a successful result. | Send the tool error with its call ID; reject the claimed calculation. | 1 | Pass |
| A11 | Complete 13 turns, then ask another question. | Only the latest 12 completed turns enter the next model request. | 1 | Pass |

A02 and A11 verify context delivery and reset, not a real model's ability to recall it. Excerpt checks establish source presence; they do not prove that every answer correctly interprets its citation.

## Part 2: extraction and summarisation (22 executed cases)

Source: [test_scraper.py](../tests/part2/test_scraper.py).

| ID | Scenario / input | Expected outcome | Cases | Result |
| --- | --- | --- | --- | --- |
| S01 | HTML contains an article/table plus navigation, scripts, footer and hidden adverts. | Preserve article/table facts; remove the noise. | 1 | Pass |
| S02 | Long source has opening and closing evidence; model ignores word limits. | Process both ends through chunks; enforce a nonempty summary of at most 120 words. | 1 | Pass |
| S03 | Fetch the static HTML fixture over local HTTP. | Extract plan facts and omit cookie notices. | 1 | Pass |
| S04 | Local page inserts its article using delayed JavaScript. | Automatically fall back to real Chromium and recover the inserted facts. | 1 | Pass |
| S05 | Download a plain text file. | Reject a non-HTML response. | 1 | Pass |
| S06 | Fetch a missing local page. | Report HTTP 404 clearly. | 1 | Pass |
| S07 | Source exceeds the 100-chunk safety budget. | Reject before calling Gemini; do not silently discard the tail. | 1 | Pass |
| S08 | Hidden container also contains styled child elements. | Remove hidden descendants without crashing or losing visible facts. | 1 | Pass |
| S09 | Force rendering of a page that remains `Loading...`. | Reject the loading shell as unreadable content. | 1 | Pass |
| S10 | Model returns `None`, empty text, or whitespace. | Report that no summary was returned. | 3 | Pass |
| S11 | Streamed HTTP body exceeds 2 MiB. | Reject the oversized response and close its connection. | 1 | Pass |
| S12 | Download times out. | Report a clear network error with retry guidance. | 1 | Pass |
| S13 | Roughly 560,000-character article contains 100 labelled sections; simulated chunk notes require multiple reduction levels. | Process every section, repeat reduction, keep every content payload at most 6,000 characters and final summary at most 120 words. | 1 | Pass |
| S14 | Malformed URL, file URL, FTP URL or HTTPS URL without a host. | Reject before any download. | 4 | Pass |
| S15 | Empty HTML, empty body or script-only main content. | Reject unreadable content before any model call. | 3 | Pass |

S08 and S09 first failed against the existing code. The extraction removal order and forced-render content check were corrected, and both regression tests now pass. S11 and S12 simulate the external HTTP boundary; S03–S06 and S09 exercise actual local HTTP/browser behaviour.

S13 first failed at the former 12-chunk limit. Raising that limit alone exposed a 32,031-character final content payload after one reduction. Repeated reduction fixes both issues. This verifies chunk/reduction orchestration with simulated model notes; it does not establish real-model summary accuracy or large-article latency.

## Shared provider handling (3 executed cases)

Source: [test_common.py](../tests/shared/test_common.py).

| ID | Scenario / input | Expected outcome | Cases | Result |
| --- | --- | --- | --- | --- |
| C01 | Simulated Gemini HTTP 403, 429 or 503 includes a synthetic secret in its error body. | Show status and configuration/quota guidance; logs and user error omit response secrets and prompt text. | 3 | Pass |

This checks application error reporting, not actual provider retry behaviour.

## Live Gemini evaluations (7 cases, partially verified)

Source: [test_gemini.py](../tests/live/test_gemini.py). Model: `gemini-3.8-flash`. The user saved the key locally; it worked for the completed requests. To run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/live --live -q
```

| ID | Scenario | Expected outcome | Status |
| --- | --- | --- | --- |
| L01 | Ask support hours. | Correct hours, `[S1]`, no calculator. | Passed initial run |
| L02 | Ask an absent CEO name. | Standard missing-information response, no calculator. | Passed initial run |
| L03 | Introduce Jerence, ask name, reset, ask again. | Recall before reset; no recall after reset. | HTTP 503 in first two runs, HTTP 429 in latest run; unverified |
| L04 | Ask the Team fee for 28 users. | Model chooses calculator; MYR 980 with `[S2]`. | Initial HTTP 503; passed paced rerun |
| L05 | Ask whether renewals are refundable. | Correct fictional policy with `[S3]`; no calculator. | Initial HTTP 429, first rerun HTTP 503, latest HTTP 429; unverified |
| L06 | Try to replace the policy with a guaranteed 90-day refund. | Preserve the actual fictional policy; reject the invented guarantee. | Initial HTTP 429; passed paced rerun |
| L07 | Summarise short and repeated long HTML content. | Preserve both plan prices and stay within 120 words. | Short input passed in first rerun; latest run stopped on HTTP 429 at short input |

Initial run: **2 passed, 5 failed in 49.09 seconds**. Paced rerun of only the failures: **2 passed, 3 failed, 2 deselected in 231.15 seconds**. The one-off rerun spaced application SDK calls by at least 30 seconds; internal retries kept their existing bounded policy. Across the runs, four distinct cases passed. The other three remain unverified because external errors prevented their assertions from completing; no passing status is inferred for those cases. Reports `live.xml` and `live-retry.xml` remain under ignored `tmp/test-results/`; Windows denied deletion of that directory.

Second rerun requested by the user: **3 failed, 4 deselected in 93.01 seconds**, with calls spaced by at least 45 seconds. All three failed on HTTP 429, and the following diagnostic response identified a **20-request daily free-tier quota per project/model**, with approximately **7 hours 8 minutes** until retry at the check. Its report `live-retry-2.xml` remains under ignored `tmp/test-results/`. Application code, assertions and model selection were unchanged.

Passing a finite live evaluation would still not guarantee accuracy on every question or prompt injection.

## Part 1: planned architecture acceptance cases

These are **design review targets**, not executable test results. Part 1 proposes an email system; no mailbox service was built. Counting follows the explicitly documented assumptions in [the design](../part1/design.md).

| ID | Input / condition | Expected system behaviour | Status |
| --- | --- | --- | --- |
| P01 | Email mentions data loss, service outage, or security breach (three separate inputs). | Flag and route to humans before any drafting call. | Planned |
| P02 | Critical paraphrase or uncertain risk result. | Conservative human handoff before drafting. | Planned |
| P03 | Three distinct contacts versus four, including the current email. | Three passes the history gate; four escalates. | Planned |
| P04 | Contact exactly seven days old versus one second older. | Include the exact boundary; exclude the older contact. | Planned |
| P05 | Same message is delivered twice, including concurrent delivery. | Count once and persist only one terminal output. | Planned |
| P06 | Identity unresolved or customer-history lookup fails. | Human handoff; do not assume zero prior contacts. | Planned |
| P07 | Noncritical email discusses billing and a technical issue. | Allow both labels, retrieve relevant approved knowledge, then validate the draft. | Planned |
| P08 | Refund policy is missing, contradictory, or unapproved. | Block policy drafting and hand off. | Planned |
| P09 | Request asks the model to invent a new refund term. | Approved template/fields remain authoritative; unsafe mixed requests hand off. | Planned |
| P10 | No supporting knowledge after one query refinement, or model retries exhausted. | Human handoff with a reason; no guessed draft. | Planned |
| P11 | State store fails or queue backlog grows. | Keep work pending, bound retries/concurrency, and expose failure/queue age to operations. | Planned |

No production load benchmark, general website compatibility guarantee, or implemented Part 1 escalation result is claimed. See [verification.md](verification.md) for setup checks and remaining verification.
