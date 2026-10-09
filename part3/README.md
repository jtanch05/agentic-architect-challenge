# Document question-answering agent

The agent answers questions using a fictional OrbitDesk support handbook. The document is short and divided into numbered sections. The full document is included in Gemini's system instruction, so this small example does not need a separate search index or vector database.

## Run

From the repository root, after installing dependencies and configuring `.env`:

```powershell
python -m part3.agent
```

Try these questions in the same session:

```text
My name is Jerence.
What is my name?
What are the support hours?
What is the monthly Team plan fee for 28 users, excluding taxes?
Are renewal payments refundable?
Who is OrbitDesk's CEO?
/reset
What is my name?
/quit
```

These questions show the agent remembering a name, answering questions from the document, using a calculator for arithmetic, and handling missing information. After `/reset`, the agent should no longer remember the earlier name. The terminal shows a waiting spinner, then the answer and tools used.

For application diagnostics, run `python -m part3.agent --verbose`. This replaces the spinner with JSON events on standard error for response times, errors, tool use and retained-turn counts. HTTP information messages stay hidden. Application events omit prompts and credentials; they are not saved to a file automatically.

## How the agent chooses a tool

Gemini receives a description of the calculator with function-calling mode set to `AUTO`. It decides whether a question needs arithmetic. Python runs the calculator, returns the result to Gemini, and lets the model finish its answer or respond to an invalid calculation.

This gives the model a limited set of actions. The code does not choose the calculator by looking for particular words in the question. Each question allows up to two tool calls and three model requests, excluding the SDK's limited retries.

The calculator reads the structure of an arithmetic expression instead of running it with `eval`. It supports numbers, parentheses, addition, subtraction, multiplication and division. It rejects names, function calls, powers, non-finite results, and division by zero.

## Conversation memory

Each agent keeps the latest 12 completed conversation turns. Previous user messages and model replies are included with the next question. Tool messages stay with the same conversation turn, including Gemini function-call details and thought signatures needed for follow-up requests.

Memory lasts only for the current session. `/reset` or closing the program clears it. Information from an older turn may be forgotten after that turn is removed from the 12-turn history.

## Checking answers against the document

Gemini returns a JSON response that identifies whether the answer comes from the document, conversation memory, a calculation, or missing information.

An answer based on the document must include a real section ID and an exact supporting quote. If the evidence fails these checks, the answer is not shown. Questions the document cannot answer receive a standard missing-information response. Calculation answers require a successful calculator result.

These checks reduce unsupported answers, but a matching quote does not prove that the model interpreted it correctly. The model also decides whether an answer comes from conversation memory. Live model checks and human review are still needed; this approach cannot guarantee that every answer is correct.

## Limits and error handling

The document is limited to 24,000 characters and each question to 2,000 characters. Answers have length limits, errors are shown clearly, and failed turns are not stored in the conversation history.

Gemini requests have a 30-second timeout and at most two attempts for selected transient HTTP failures. HTTP 429 is not automatically retried: check usage and wait for the applicable rate or quota limit to reset. HTTP 504 is reported as a provider timeout. These are per-request limits, not a deadline for an entire conversation turn.

An offline check exercises 20 sequential requests with 20 ms simulated provider delays and three injected timeouts. It verifies recovery, latency events and the 12-turn memory limit. It does not measure real Gemini latency, concurrent capacity or production throughput.

To use another UTF-8 document, give its sections numbered labels such as `[S1]` and `[S2]`, then run:

```powershell
python -m part3.agent --document FILE
```

The approved refund-template process in Part 1 is a separate proposed design. This document agent does not include that production safeguard.
