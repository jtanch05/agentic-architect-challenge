"""Offline Part 3 cases: document evidence, memory and calculator handling."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.genai import types

from part3.agent import DocumentAgent


def model_response(text):
    content = types.Content(role="model", parts=[types.Part.from_text(text=text)])
    return SimpleNamespace(function_calls=None, candidates=[SimpleNamespace(content=content)], text=text)


def test_document_answer_includes_verified_source():
    client = Mock()
    client.models.generate_content.return_value = model_response(
        '{"kind":"document","answer":"Email support@example.test.",'
        '"sources":[{"section":"S1","quote":"Contact support@example.test."}]}'
    )
    agent = DocumentAgent(client, "test-model", "[S1] Contact support@example.test.")
    answer = agent.ask("How do I contact support?")
    assert "support@example.test" in answer
    assert "[S1]" in answer
    assert agent.last_tools == []


def test_name_context_is_available_on_later_turn():
    def reply(**request):
        messages = request["contents"]
        previous_text = " ".join(p.text or "" for m in messages for p in m.parts)
        answer = "Your name is Jerence." if "My name is Jerence" in previous_text else "I do not know."
        return model_response(json.dumps({"kind": "memory", "answer": answer, "sources": [],
                                          "memory_quote": "My name is Jerence." if "My name is Jerence" in previous_text else ""}))

    client = Mock()
    client.models.generate_content.side_effect = reply
    agent = DocumentAgent(client, "test-model", "[S1] Contact support@example.test.")
    agent.ask("My name is Jerence.")
    assert "Jerence" in agent.ask("What is my name?")
    agent.reset()
    assert "Jerence" not in agent.ask("What is my name?")


def test_arithmetic_executes_selected_calculator_and_returns_result():
    call = types.FunctionCall(name="calculator", args={"expression": "35 * 28"})
    content = types.Content(role="model", parts=[types.Part(function_call=call)])

    def final_reply(**request):
        results = [p.function_response for m in request["contents"] for p in m.parts if p.function_response]
        assert results[-1].response["result"] == 980
        return model_response('{"kind":"calculation","answer":"980","sources":[]}')

    client = Mock()
    responses = iter([SimpleNamespace(function_calls=[call], candidates=[SimpleNamespace(content=content)], text=None)])
    client.models.generate_content.side_effect = lambda **kwargs: next(responses, None) or final_reply(**kwargs)
    agent = DocumentAgent(client, "test-model", "[S1] The Team plan costs MYR 35.")
    assert "980" in agent.ask("What is 35 times 28?")
    assert agent.last_tools == ["calculator"]


@pytest.mark.parametrize("kind", ["calculation", "document", "memory"])
def test_model_cannot_replace_the_calculator_result(kind):
    call = types.FunctionCall(name="calculator", args={"expression": "35 * 28"})
    content = types.Content(role="model", parts=[types.Part(function_call=call)])
    client = Mock()
    client.models.generate_content.side_effect = [
        SimpleNamespace(function_calls=[call], candidates=[SimpleNamespace(content=content)], text=None),
        model_response(json.dumps({"kind": kind, "answer": "The fee is 9800.", "sources": [
            {"section": "S1", "quote": "Team costs MYR 35."},
        ]})),
    ]
    agent = DocumentAgent(client, "test-model", "[S1] Team costs MYR 35.")
    if kind == "calculation":
        answer = agent.ask("What is the Team fee for 28 users?")
        assert "980" in answer and "9800" not in answer and "[S1]" in answer
    else:
        with pytest.raises(RuntimeError, match="invalid answer"):
            agent.ask("What is the Team fee for 28 users?")
        assert agent.turns == []


@pytest.mark.parametrize("quote", ["", "My name is Invented.", "Refunds are guaranteed for 90 days."])
def test_memory_label_cannot_authorize_an_unsupported_document_claim(quote):
    from part3.agent import UNKNOWN

    client = Mock()
    client.models.generate_content.return_value = model_response(json.dumps({
        "kind": "memory", "answer": "Refunds are guaranteed for 90 days.",
        "sources": [], "memory_quote": quote,
    }))
    agent = DocumentAgent(client, "test-model", "[S1] Refund requests must be made within 14 days.")
    assert agent.ask("What is the refund policy?") == UNKNOWN


def test_memory_answer_is_rendered_from_user_evidence_not_model_prose():
    client = Mock()
    client.models.generate_content.return_value = model_response(json.dumps({
        "kind": "memory", "answer": "Your name is Invented. Refunds last 90 days.",
        "sources": [], "memory_quote": "My name is Jerence.",
    }))
    agent = DocumentAgent(client, "test-model", "[S1] Example.")
    answer = agent.ask("My name is Jerence.")
    assert "Jerence" in answer
    assert "Invented" not in answer and "90" not in answer


@pytest.mark.parametrize("context,question", [
    ("Call me Jerence.", "What should you call me?"),
    ("Prefer short answers, please.", "What answer style do I prefer?"),
])
def test_memory_accepts_user_context_without_a_required_prefix(context, question):
    from part3.agent import UNKNOWN

    client = Mock()
    client.models.generate_content.return_value = model_response(json.dumps({
        "kind": "memory", "answer": "Personal context.", "sources": [], "memory_quote": context,
    }))
    agent = DocumentAgent(client, "test-model", "[S1] Example.")
    assert agent.ask(context) == f"You said: {context}"
    assert agent.ask(question) == f"You said: {context}"
    agent.reset()
    assert agent.ask(question) == UNKNOWN


def test_memory_can_recall_updated_name_and_reset_removes_evidence():
    client = Mock()
    replies = ["My name is Jerence.", "My name is Alex now.", "My name is Alex now.", "My name is Alex now."]
    client.models.generate_content.side_effect = [model_response(json.dumps({
        "kind": "memory", "answer": "Personal context.", "sources": [], "memory_quote": quote,
    })) for quote in replies]
    agent = DocumentAgent(client, "test-model", "[S1] Example.")
    agent.ask("My name is Jerence.")
    agent.ask("My name is Alex now.")
    assert "Alex" in agent.ask("What is my name?")
    agent.reset()
    assert "Alex" not in agent.ask("What is my name?")


def test_assistant_text_cannot_be_used_as_personal_memory_evidence():
    from part3.agent import UNKNOWN

    client = Mock()
    client.models.generate_content.side_effect = [
        model_response('{"kind":"document","answer":"My name is Invented.","sources":[{"section":"S1","quote":"Example."}]}'),
        model_response('{"kind":"memory","answer":"Invented","sources":[],"memory_quote":"My name is Invented."}'),
    ]
    agent = DocumentAgent(client, "test-model", "[S1] Example.")
    agent.ask("What does the document say?")
    assert agent.ask("What is my name?") == UNKNOWN


@pytest.mark.parametrize("expression", ["1 / 0", "__import__('os').getcwd()", "2 ** 1000", "1e309"])
def test_calculator_rejects_unsafe_or_invalid_arithmetic(expression):
    from part3.agent import calculator

    with pytest.raises(ValueError):
        calculator(expression)


def test_unverified_document_quote_is_withheld():
    client = Mock()
    client.models.generate_content.return_value = model_response(
        '{"kind":"document","answer":"Refunds last 90 days.",'
        '"sources":[{"section":"S1","quote":"Refunds last 90 days."}]}'
    )
    agent = DocumentAgent(client, "test-model", "[S1] Refund requests must be made within 14 days.")
    assert "could not find" in agent.ask("Can I get a refund after 90 days?")


def test_tool_loop_stops_at_budget_and_does_not_save_failed_turn():
    call = types.FunctionCall(name="calculator", args={"expression": "1+1"})
    content = types.Content(role="model", parts=[types.Part(function_call=call)])
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(
        function_calls=[call], candidates=[SimpleNamespace(content=content)], text=None,
    )
    agent = DocumentAgent(client, "test-model", "[S1] Example.")
    with pytest.raises(RuntimeError, match="limit"):
        agent.ask("What is 1+1?")
    assert len(agent.last_tools) == 2
    assert agent.turns == []


def test_api_timeout_has_clear_error_and_preserves_completed_context():
    import httpx

    client = Mock()
    client.models.generate_content.return_value = model_response('{"kind":"memory","answer":"Hello Jerence.","sources":[],"memory_quote":"My name is Jerence."}')
    agent = DocumentAgent(client, "test-model", "[S1] Example.")
    agent.ask("My name is Jerence.")
    client.models.generate_content.side_effect = httpx.ReadTimeout("simulated timeout")
    with pytest.raises(RuntimeError, match="timed out"):
        agent.ask("What is my name?")
    assert len(agent.turns) == 1


@pytest.mark.parametrize("bad_reply", [
    "not JSON", "[]", '{"kind":"document"}',
    '{"kind":"document","answer":"Hello","sources":"S1"}',
    '{"kind":"other","answer":"Hello","sources":[]}',
    '{"kind":"memory","answer":"","sources":[]}',
])
def test_malformed_model_reply_is_reported_and_next_question_can_succeed(bad_reply):
    client = Mock()
    client.models.generate_content.side_effect = [
        model_response(bad_reply),
        model_response('{"kind":"document","answer":"Email support@example.test.",'
                       '"sources":[{"section":"S1","quote":"Contact support@example.test."}]}'),
    ]
    agent = DocumentAgent(client, "test-model", "[S1] Contact support@example.test.")
    with pytest.raises(RuntimeError, match="invalid answer"):
        agent.ask("How do I contact support?")
    assert "support@example.test" in agent.ask("Please try again.")
    requests = client.models.generate_content.call_args_list
    assert len(requests[-1].kwargs["contents"]) == 1


@pytest.mark.parametrize("sources", [[], [{"section": "S99", "quote": "Team costs MYR 35."}],
                                    [{"section": "S1", "quote": " "}]])
def test_missing_or_invalid_evidence_cannot_authorize_document_answer(sources):
    from part3.agent import UNKNOWN

    client = Mock()
    client.models.generate_content.return_value = model_response(json.dumps({
        "kind": "document", "answer": "Team costs MYR 35.", "sources": sources,
    }))
    agent = DocumentAgent(client, "test-model", "[S1] Team costs MYR 35.")
    assert agent.ask("What does Team cost?") == UNKNOWN


def test_failed_calculator_is_returned_to_model_and_cannot_authorize_a_result():
    call = types.FunctionCall(name="calculator", id="failed-call", args={"expression": "1 / 0"})
    content = types.Content(role="model", parts=[types.Part(function_call=call)])

    def reply_to_error(**request):
        result = request["contents"][-1].parts[0].function_response
        assert result.id == "failed-call"
        assert "error" in result.response and "result" not in result.response
        return model_response('{"kind":"calculation","answer":"The result is 42.","sources":[]}')

    client = Mock()
    responses = iter([SimpleNamespace(function_calls=[call], candidates=[SimpleNamespace(content=content)], text=None)])
    client.models.generate_content.side_effect = lambda **kwargs: next(responses, None) or reply_to_error(**kwargs)
    agent = DocumentAgent(client, "test-model", "[S1] Example.")
    with pytest.raises(RuntimeError, match="invalid answer"):
        agent.ask("What is 1 / 0?")
    assert agent.last_tools == ["calculator"]


def test_later_calculation_failure_cannot_reuse_an_earlier_success():
    responses = []
    for expression in ("2 + 2", "1 / 0"):
        call = types.FunctionCall(name="calculator", args={"expression": expression})
        content = types.Content(role="model", parts=[types.Part(function_call=call)])
        responses.append(SimpleNamespace(function_calls=[call], candidates=[SimpleNamespace(content=content)], text=None))
    responses.append(model_response('{"kind":"calculation","answer":"4","sources":[]}'))
    client = Mock()
    client.models.generate_content.side_effect = responses
    agent = DocumentAgent(client, "test-model", "[S1] Example.")
    with pytest.raises(RuntimeError, match="invalid answer"):
        agent.ask("Calculate 2 + 2, then 1 / 0.")
    assert agent.turns == []


def test_context_budget_keeps_latest_twelve_completed_turns():
    client = Mock()
    client.models.generate_content.side_effect = lambda **request: model_response(json.dumps({
        "kind": "memory", "answer": "Context acknowledged.", "sources": [],
        "memory_quote": request["contents"][-1].parts[0].text,
    }))
    agent = DocumentAgent(client, "test-model", "[S1] Example.")
    for index in range(13):
        agent.ask(f"Remember context-{index:02d}.")
    agent.ask("Remember the latest context.")
    messages = client.models.generate_content.call_args.kwargs["contents"]
    text = " ".join(part.text or "" for message in messages for part in message.parts)
    assert "context-00" not in text
    assert all(f"context-{index:02d}" in text for index in range(1, 13))


def test_sequential_slow_provider_requests_recover_and_keep_memory_bounded(caplog):
    import logging
    import time
    import httpx

    client = Mock()
    completed = 0

    def slow_reply(**request):
        time.sleep(0.02)
        if client.models.generate_content.call_count in {4, 9, 16}:
            raise httpx.ReadTimeout("simulated provider timeout")
        return model_response(json.dumps({"kind": "memory", "answer": "Acknowledged.", "sources": [],
                                          "memory_quote": request["contents"][-1].parts[0].text}))

    client.models.generate_content.side_effect = slow_reply
    agent = DocumentAgent(client, "test-model", "[S1] Example.")
    with caplog.at_level(logging.INFO, logger="assessment"):
        for index in range(20):
            previous_turns = list(agent.turns)
            if index + 1 in {4, 9, 16}:
                with pytest.raises(RuntimeError, match="timed out"):
                    agent.ask(f"Remember item {index}.")
                assert agent.turns == previous_turns
            else:
                agent.ask(f"Remember item {index}.")
                completed += 1
            assert len(agent.turns) == min(completed, 12)
    events = [json.loads(record.message) for record in caplog.records if record.name == "assessment"]
    requests = [event for event in events if event["event"] in {"model_response", "model_error"}]
    assert len(requests) == 20
    assert sum(event["event"] == "model_error" for event in requests) == 3
    assert all(event["latency_ms"] >= 10 for event in requests)


@pytest.mark.parametrize("verbose", [False, True])
def test_cli_diagnostics_are_opt_in(verbose):
    import subprocess
    import sys
    from common import ROOT

    script = '''
import logging
from unittest.mock import Mock, patch
from part3 import agent
from common import log_event
def answer(question):
    log_event("agent_answer", tools=[], retained_turns=1)
    logging.getLogger("httpx").info("HTTP diagnostic must stay hidden")
    return "Hello."
fake = Mock(last_tools=[])
fake.ask.side_effect = answer
with patch.object(agent, "create_client", return_value=(Mock(), "test-model")), patch.object(agent, "DocumentAgent", return_value=fake), patch("builtins.input", side_effect=["hello", "/quit"]):
    agent.main()
'''
    result = subprocess.run([sys.executable, "-c", script] + (["--verbose"] if verbose else []),
                            cwd=ROOT, capture_output=True, text=True, check=True)
    assert "Agent: Hello." in result.stdout
    assert ('"event": "agent_answer"' in result.stderr) == verbose
    assert "HTTP diagnostic must stay hidden" not in result.stderr
