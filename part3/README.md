# Document question-answering agent

The agent answers questions using a fictional ClearDesk support handbook. The handbook is short and divided into numbered sections. The full document is included in Gemini's system instruction, which defines how the agent should respond. This small example therefore does not need a separate search index or vector database.

## Run

Complete the [local setup](../README.md#local-setup), then run these commands from the repository root. Activate the environment in each new terminal session:

```powershell
.\.venv\Scripts\Activate.ps1
python -m part3.agent
```

If PowerShell blocks activation, run `.\.venv\Scripts\python.exe -m part3.agent` directly. This uses the project's installed packages without activating the environment.

Try these questions in the same session:

```text
My name is Jerence.
What is my name?
What are the support hours?
What is the monthly Team plan fee for 28 users, excluding taxes?
Are renewal payments refundable?
Who is ClearDesk's CEO?
/reset
What is my name?
/quit
```

These questions show the agent remembering a name, answering questions from the document, using a calculator for arithmetic, and handling missing information. After `/reset`, the agent should no longer remember the earlier name. The terminal shows a waiting spinner, then the answer and tools used.

To view diagnostic logs, run `python -m part3.agent --verbose`. This replaces the spinner with JSON events showing response times, errors, tool use and the number of turns kept in memory. These events appear on standard error. HTTP information messages remain hidden, and application events exclude prompts and credentials. Logs are not saved to a file automatically.

## How the agent chooses a tool

Gemini receives a description of the calculator, with function-calling mode set to `AUTO`. The model decides whether a question needs arithmetic. If it requests a calculation, Python runs the tool and returns the result to Gemini. The model can then finish its answer or respond to a calculation error.

For a valid calculation answer, Python displays the actual expression and tool result, for example `35 * 28 = 980`. If Gemini writes 9800 in its final answer, that text does not replace the calculated value. Valid document references are kept. After a successful calculation, the code rejects a final answer labelled as document knowledge or memory.

The model chooses whether to call the calculator; the code does not make that choice by checking for keywords. Each question allows up to two tool calls and three model requests. These counts exclude the SDK's limited automatic retries.

`ask()` manages model requests and saves completed turns. `_execute_tools()` runs the requested calculator calls and prepares their responses for Gemini. Separate helpers parse the final JSON, verify memory quotes and check document sources. `validate_answer()` applies these checks before returning an answer.

The calculator checks the structure of an arithmetic expression instead of executing it with `eval`. It supports numbers, parentheses, addition, subtraction, multiplication and division. It rejects names, function calls, powers, division by zero and results that are infinite or not a number.

## Conversation memory

The agent keeps the latest 12 completed conversation turns. A turn contains the user's question, any tool messages and the model's reply. This recent history is included with the next question. Tool messages retain the function-call details and Gemini metadata needed for follow-up requests.

Memory lasts only for the current session. `/reset` or closing the program clears it. Information from an older turn may be forgotten after that turn is removed from the 12-turn history.

Use `/quit` or `/exit` to close the program. Completed replies are stored as JSON containing the validated answer, so later requests receive a consistent response format and the actual calculator result.

A memory answer must include an exact quote from a user message still in memory or from the current input, such as "Call me Jerence." Quotes from assistant replies and invented text are rejected. For a simple introduction such as "My name is Jerence" or "Call me Jerence", Python replies "Your name is Jerence." using the verified name. Other memory replies display the verified quote as `You said: ...`, rather than the model's freely written answer. This attributes the statement to the user and does not treat it as verified company policy.

The agent can also recall an earlier request. For example, asking what was calculated earlier can return the original arithmetic expression as a user quote without running the calculator again.

## Checking answers against the document

Gemini returns a JSON response that identifies whether the answer comes from the document, conversation memory, a calculation, or missing information.

An answer based on the document must include an existing section ID and an exact quote from that section. If these checks fail, the proposed answer is withheld. Questions the document cannot answer receive a standard message explaining that the information was not found. Calculation answers require a successful tool result and display its actual value. Memory answers use verified excerpts from user messages, with natural wording for simple name introductions.

These checks reduce unsupported answers, but finding a matching quote does not prove that the model understood it correctly. Gemini still chooses the calculator inputs and the memory quote. The code checks that the quote exists, but does not prove that it is relevant, up to date or personal information. It also does not prove that the calculation matches the question. Live model tests and human review are still needed.

## Limits and error handling

The document is limited to 24,000 characters and each question to 2,000 characters. Answers have length limits, errors are shown clearly, and failed turns are not stored in the conversation history.

Each Gemini attempt has a 30-second timeout. Selected temporary HTTP errors allow up to two attempts. HTTP 429 is not retried automatically; check your usage and wait for the rate or quota limit to reset. HTTP 504 is reported as a provider timeout. These limits apply to individual attempts, rather than the entire conversation turn.

An offline test sends 20 requests in sequence, with a simulated 20 ms delay per request and three simulated timeouts. It checks recovery after errors, response-time logs and the 12-turn memory limit. It does not measure real Gemini response times or performance with multiple users.

To use another UTF-8 document, give its sections numbered labels such as `[S1]` and `[S2]`, then run:

```powershell
python -m part3.agent --document FILE
```

The approved refund-template process in Part 1 is a separate proposed design. This document agent does not include that production safeguard.
