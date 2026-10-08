# Document agent

The sample document is a fictional OrbitDesk support handbook. It is deliberately small and divided into numbered sections. The complete document is included in Gemini's system instruction, avoiding an unnecessary vector database and retrieval implementation for one short document.

## Run

From the repository root with dependencies and `.env` configured:

```powershell
python -m part3.agent
```

Try these in the same session:

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

The terminal displays the answer and actual selected tools. Logs show tool execution and model latency without storing prompts or credentials.

## Agentic behavior

Gemini receives the calculator definition with function-calling mode AUTO. It decides whether arithmetic is needed. Python executes only the supported calculator, returns the result to Gemini, and lets the model finish or correct invalid arithmetic. This is a bounded reasoning/action loop, rather than a keyword-based tool switch. There is a limit of two tool calls and three model requests per question, excluding the SDK's bounded retry attempts.

The calculator parses an arithmetic syntax tree; it never calls `eval`. It accepts numbers, parentheses, +, -, * and /; names, function calls, exponentiation, non-finite results and division by zero are rejected.

## Memory and grounding

Each agent instance retains the latest 12 completed turns in memory. Earlier user/model messages are sent with the next question. Tool messages are kept together with their turn, preserving complete Gemini function-call messages and thought signatures. `/reset` and process exit clear memory. It is session context, not persistent identity storage; a name mentioned only in an older discarded turn may be forgotten.

Final answers have a JSON shape describing document, memory, calculation or unknown answers. Document answers require a real section ID and an exact supporting excerpt; invalid evidence is withheld. Unknown questions receive a standard missing-information response. Calculations require a successful tool result. Model output is checked in code, but source matching does not prove that every answer semantically follows from its excerpt. Memory-answer classification also relies on the model. Live evaluations and human review remain necessary; this is not a guarantee against all hallucinations.

The handbook is capped at 24,000 characters and questions at 2,000. Answers are bounded, errors are shown clearly, and failed turns are not added to completed conversation history. Provide another UTF-8 document with numbered `[S1]`, `[S2]` sections using `--document FILE`.

The production refund-template safeguard described in Part 1 is a separate proposed design, not a feature of this general document agent.
