# Assessment test cases

Latest offline run: 9 October 2026. Earlier live runs: 9 October 2026. Windows, Python 3.13.1.

**Latest result: 64 passed, 8 live cases skipped in 12.29 seconds.** The local report is saved at `tmp/test-results/after-refactor.xml`. This is the time taken to run the test suite, not a measure of production performance. Each input in a parameterised test counts as a separate pytest case.

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml=tmp/test-results/after-refactor.xml
```

The XML report can be regenerated under `tmp/`, which is excluded from Git. Tests call the actual application code and simulate responses where it calls the Gemini SDK. Tests for downloading and rendering pages use local sample files and real headless Chromium. This run did not use an external website or the live Gemini API.

The same 64 tests passed before the code was reorganised, with eight live cases skipped, in 13.21 seconds. That report is saved at `tmp/test-results/before-refactor.xml`. The tests were unchanged between these runs.

## Part 3: document agent (36 executed cases)

Source: [test_agent.py](../tests/part3/test_agent.py).

| ID | Scenario / input | Expected outcome | Cases | Result |
| --- | --- | --- | --- | --- |
| A01 | Ask how to contact support; model supplies a matching excerpt. | Answer includes the supported address and `[S1]`; no tool runs. | 1 | Pass |
| A02 | State a name, ask for it later, then reset. | Prior name context is available to the model; reset removes it. | 1 | Pass |
| A03 | Model selects `calculator("35 * 28")`. | The tool returns 980; the answer is accepted and the tool use is recorded. | 1 | Pass |
| A04 | Calculator receives `1 / 0`, a Python import/call, `2 ** 1000`, or `1e309`. | Reject each expression with a controlled error. | 4 | Pass |
| A05 | Model cites an invented 90-day refund excerpt. | Withhold the unsupported answer. | 1 | Pass |
| A06 | Model repeatedly requests calculation. | Stop at the two-tool budget; do not retain the failed turn. | 1 | Pass |
| A07 | API times out after a completed name turn. | Clear connection error; earlier completed context remains. | 1 | Pass |
| A08 | Reply is non-JSON, a JSON list, missing fields, wrongly typed sources, an unknown kind, or an empty answer; then a valid reply arrives. | Report invalid output, exclude the failed turn, and allow the next question to succeed. | 6 | Pass |
| A09 | Document answer has no sources, a nonexistent section, or a blank quote. | Withhold the answer in each case. | 3 | Pass |
| A10 | Calculator divides by zero; model then claims a successful result. | Send the tool error with its call ID; reject the claimed calculation. | 1 | Pass |
| A11 | Complete 13 turns, then ask another question. | Only the latest 12 completed turns enter the next model request. | 1 | Pass |
| A12 | 20 sequential requests, each delayed by 20 ms; requests 4, 9 and 16 time out. | Failed turns leave memory unchanged; later requests succeed; memory stays within 12 completed turns; all 20 requests have latency events. | 1 | Pass |
| A13 | Run the CLI with and without `--verbose`, using a fake agent. | Both print answers; only verbose mode prints application events; HTTP information messages stay hidden. | 2 | Pass |
| A14 | Calculator returns 980; model claims 9800 and labels the answer as calculation, document or memory. | Display the actual tool value for a calculation; reject the document and memory labels. | 3 | Pass |
| A15 | Model labels an invented refund statement as memory, with missing or fabricated personal evidence. | Withhold unsupported memory answers. | 3 | Pass |
| A16 | Model supplies a valid user quote but invents additional name or policy claims. | Display only the verified user quote and exclude the invented claims. | 1 | Pass |
| A17 | User changes name, asks for it, then resets; model tries the old excerpt again. | Accept the verified updated excerpt before reset and reject it after reset. | 1 | Pass |
| A18 | Personal excerpt exists only in an assistant reply. | Reject it as user-memory evidence. | 1 | Pass |
| A19 | A calculation succeeds, a later calculation fails, and the model presents the earlier result as the answer. | Reject the answer and do not save the failed turn. | 1 | Pass |
| A20 | User says "Call me Jerence" or "Prefer short answers, please", asks for that context, then resets. | Accept verified user excerpts without a required prefix; reject them after reset. | 2 | Pass |

A02 and A11 check that the code passes recent context to the model and clears it on reset. They do not test a real model's ability to remember it. Quote checks confirm that the text exists in the stated source, but do not prove that the answer interprets it correctly.

A12 checks recovery when requests run one at a time with simulated delays. It does not measure performance with multiple users or real Gemini requests. The simulated provider raises the timeouts directly, so the test does not verify the SDK's actual 30-second timeout.

A14–A16 and A19 failed before the missing checks were added. A20 failed before the unnecessary wording restriction was removed. A17–A18 check name changes, reset and rejection of quotes found only in assistant replies. Displaying actual tool results prevents the model from replacing those values, but does not prove it chose the right calculation. A verified memory quote shows what a user said; it does not establish relevance, whether the information is current or the truth of a company-policy claim.

## Part 2: extraction and summarisation (23 executed cases)

Source: [test_scraper.py](../tests/part2/test_scraper.py).

| ID | Scenario / input | Expected outcome | Cases | Result |
| --- | --- | --- | --- | --- |
| S01 | HTML contains an article/table plus navigation, scripts, footer and hidden adverts. | Preserve article/table facts; remove the noise. | 1 | Pass |
| S02 | Long source has opening and closing evidence; model ignores word limits. | Process both ends through chunks; enforce a nonempty summary of at most 120 words. | 1 | Pass |
| S03 | Fetch the static HTML fixture over local HTTP. | Extract plan facts and omit cookie notices. | 1 | Pass |
| S04 | Local page inserts its article using delayed JavaScript. | Automatically fall back to real Chromium and recover the inserted facts. | 1 | Pass |
| S05 | Download a plain text file. | Reject a non-HTML response. | 1 | Pass |
| S06 | Fetch a missing local page. | Report HTTP 404 clearly. | 1 | Pass |
| S07 | Source exceeds the 100-chunk input limit. | Reject before calling Gemini; do not silently discard the end of the article. | 1 | Pass |
| S08 | Hidden container also contains styled child elements. | Remove hidden descendants without crashing or losing visible facts. | 1 | Pass |
| S09 | Force rendering of a page that remains `Loading...`. | Reject the loading shell as unreadable content. | 1 | Pass |
| S10 | Model returns `None`, empty text, or whitespace. | Report that no summary was returned. | 3 | Pass |
| S11 | Streamed HTTP body exceeds 2 MiB. | Reject the oversized response and close its connection. | 1 | Pass |
| S12 | Download times out. | Report a clear network error with retry guidance. | 1 | Pass |
| S13 | An article of roughly 560,000 characters contains 100 labelled sections; simulated notes need several rounds of summarisation. | Process every section, keep each content input within 6,000 characters and limit the final summary to 120 words. | 1 | Pass |
| S14 | Malformed URL, file URL, FTP URL or HTTPS URL without a host. | Reject before any download. | 4 | Pass |
| S15 | Empty HTML, empty body or script-only main content. | Reject unreadable content before any model call. | 3 | Pass |
| S16 | Saved HTML contains a price, date and non-refundable condition; a simulated summary preserves them; usage logging is enabled. | Display the supplied facts in the terminal and save call counts only to the local log, without recording page text. | 1 | Pass |

S08 and S09 failed before the fixes. Correcting the order in which hidden elements are removed and checking the rendered content made both tests pass. S11 and S12 simulate HTTP responses and errors. S03–S06 and S09 use actual local downloads or browser rendering.

S13 first failed because of the former 12-chunk limit. Raising that limit alone left a final model input of 32,031 characters after one round of summarisation. Repeated summarisation now keeps the inputs within the required size. The test uses simulated model notes, so it does not measure Gemini's summary accuracy or response time for large articles.

S16 checks that supplied facts pass through the code and appear in the output. It does not test Gemini's ability to preserve them. Separate short and long live tests check prices, support hours, a date and policy conditions. These updated tests have not been run.

## Shared provider handling (5 executed cases)

Source: [test_common.py](../tests/shared/test_common.py).

| ID | Scenario / input | Expected outcome | Cases | Result |
| --- | --- | --- | --- | --- |
| C01 | Simulated Gemini HTTP 403, 429, 503 or 504 includes a synthetic secret in its error body. | Show status-specific guidance and error latency; application logs and user error omit response secrets and prompt text. | 4 | Pass |
| C02 | Inspect client configuration using a fake client factory. | 30-second timeout, two maximum attempts, transient 503/504 retries enabled and 429 excluded. | 1 | Pass |

This checks application error reporting, not actual provider retry behaviour.

## Current live Gemini evaluations (8 cases)

After the calculator and memory improvements, a run selecting only name recall/reset and document arithmetic returned **2 failures, 6 deselected in 2.53 seconds**. Both tests stopped on HTTP 429 before the expected behaviour could be checked. They therefore remain unverified. The report is saved at `tmp/test-results/live-hardening.xml`, which is excluded from Git.

The current live suite contains six Part 3 cases and separate short and long summary cases. The summary tests check prices, support hours, dates and policy conditions. They have not been verified against Gemini. Run them separately with `-k short` or `-k long` when quota is available.

## Historical live evaluations (previous implementation, 7 cases)

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

Initial run: **2 passed, 5 failed in 49.09 seconds**. A rerun of the failed cases returned **2 passed, 3 failed, 2 deselected in 231.15 seconds**. That rerun placed at least 30 seconds between application calls to the SDK. Automatic SDK retries kept their existing limits. Across these runs, four different cases passed. The remaining three are unverified because provider errors prevented the checks from completing. The reports `live.xml` and `live-retry.xml` are stored under `tmp/test-results/` and excluded from Git.

A second rerun returned **3 failed, 4 deselected in 93.01 seconds**, with at least 45 seconds between calls. All three tests stopped on HTTP 429. A subsequent diagnostic response reported a **20-request daily free-tier quota per project/model**, with approximately **7 hours 8 minutes** until retry at the time of the check. Its report, `live-retry-2.xml`, is stored under `tmp/test-results/` and excluded from Git. The application code, test assertions and model selection were unchanged.

Passing these live tests would not guarantee correct answers for every question or protection against every prompt-injection attempt.

## Part 1: planned architecture acceptance cases

These are **design review targets**, not executable test results. Part 1 proposes an email system; no mailbox service was built. Counting follows the explicitly documented assumptions in [the design](../part1/design.md).

| ID | Input / condition | Expected system behaviour | Status |
| --- | --- | --- | --- |
| P01 | Email mentions data loss, service outage, or security breach (three separate inputs). | Flag and route to humans before any drafting call. | Planned |
| P02 | Critical paraphrase or uncertain risk result. | Conservative human handoff before drafting. | Planned |
| P03 | Three distinct contacts versus four, including the current email. | Three passes the history gate; four escalates. | Planned |
| P04 | Contact exactly seven days old versus one second older. | Include the exact boundary; exclude the older contact. | Planned |
| P05 | The same message is delivered twice, including at the same time. | Count the contact once and save only one final outcome. | Planned |
| P06 | Identity unresolved or customer-history lookup fails. | Human handoff; do not assume zero prior contacts. | Planned |
| P07 | Noncritical email discusses billing and a technical issue. | Allow both labels, retrieve relevant approved knowledge, then validate the draft. | Planned |
| P08 | Refund policy is missing, contradictory, or unapproved. | Block policy drafting and hand off. | Planned |
| P09 | Request asks the model to invent a new refund term. | Approved template/fields remain authoritative; unsafe mixed requests hand off. | Planned |
| P10 | No supporting knowledge after one query refinement, or model retries exhausted. | Human handoff with a reason; no guessed draft. | Planned |
| P11 | The processing store fails or the queue grows. | Keep work pending, limit retries and simultaneous tasks, and report errors and waiting times to operations staff. | Planned |

No production load benchmark, general website compatibility guarantee, or implemented Part 1 escalation result is claimed. See the [test guide](../tests/README.md) for setup and execution commands; remaining live verification is recorded above.
