"""Offline Part 2 cases: extraction, browser rendering and summary limits."""

from part2.scraper import extract_text

import pytest


def test_extracts_article_and_table_without_navigation_or_scripts():
    html = """<html><body><nav>Buy now</nav><main><article><h1>Support plans</h1>
    <p>Starter costs MYR 20.</p><table><tr><td>Team</td><td>MYR 35</td></tr></table>
    <script>steal()</script><div hidden>Hidden advert</div></article></main><footer>Cookies</footer></body></html>"""
    text = extract_text(html)
    assert "Starter costs MYR 20" in text
    assert "Team MYR 35" in text
    assert all(noise not in text for noise in ["Buy now", "steal", "Hidden advert", "Cookies"])


def test_long_source_is_chunked_and_summary_is_capped_even_if_model_ignores_limit():
    from types import SimpleNamespace
    from unittest.mock import Mock
    from part2.scraper import summarize_text

    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(text="summary " * 180)
    source = "opening " + "content " * 1800 + "closing evidence"
    result = summarize_text(source, client, "test-model")
    assert result.strip()
    assert len(result.split()) <= 120
    prompts = [call.kwargs["contents"] for call in client.models.generate_content.call_args_list]
    assert any("closing evidence" in prompt for prompt in prompts)
    assert any("opening" in prompt for prompt in prompts)


def test_summary_pipeline_preserves_mocked_facts_and_logs_usage_only_to_file(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from part2 import scraper

    html = tmp_path / "facts.html"
    facts = "Team costs MYR 35 excluding taxes. Applications close on 15 October 2026. Renewal payments are non-refundable."
    html.write_text(f"<main><p>{facts}</p></main>", encoding="utf-8")
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(text=facts)
    monkeypatch.setattr(scraper, "create_client", Mock(return_value=(client, "test-model")))
    log = tmp_path / "usage.log"
    monkeypatch.setattr("sys.argv", ["scraper", "--html", str(html), "--usage-log", str(log)])
    scraper.main()
    output = capsys.readouterr()
    assert facts in output.out
    assert facts in client.models.generate_content.call_args.kwargs["contents"]
    assert '"minimum_calls": 1' in log.read_text(encoding="utf-8")
    assert '"application_calls": 1' in log.read_text(encoding="utf-8")
    assert "summary_usage_estimate" not in output.out + output.err
    assert "summary_model_calls" not in output.out + output.err
    assert facts not in log.read_text(encoding="utf-8")


def test_fetches_static_html_over_http(fixture_site):
    from part2.scraper import scrape_page

    text = scrape_page(fixture_site + "/static.html")
    assert "Starter costs MYR 20" in text
    assert "Cookie notices" not in text


def test_javascript_shell_uses_rendered_content(fixture_site):
    from part2.scraper import scrape_page

    text = scrape_page(fixture_site + "/dynamic.html")
    assert "Rendered evidence" in text
    assert "Team costs MYR 35" in text


def test_non_html_download_is_rejected(fixture_site):
    from part2.scraper import scrape_page

    with pytest.raises(ValueError, match="HTML"):
        scrape_page(fixture_site + "/not_html.txt")


def test_missing_page_reports_download_failure(fixture_site):
    from part2.scraper import scrape_page

    with pytest.raises(RuntimeError, match="404"):
        scrape_page(fixture_site + "/missing.html")


def test_over_budget_source_is_rejected_before_model_call():
    from unittest.mock import Mock
    from part2.scraper import CHUNK_CHARS, MAX_CHUNKS, summarize_text

    client = Mock()
    with pytest.raises(ValueError, match="budget"):
        summarize_text("x" * (CHUNK_CHARS * MAX_CHUNKS + 1), client, "test-model")
    client.models.generate_content.assert_not_called()


def test_very_long_article_processes_every_section_through_multiple_reduction_levels(caplog):
    import logging
    from types import SimpleNamespace
    from unittest.mock import Mock
    from part2.scraper import CHUNK_CHARS, summarize_text

    requests = []

    def reply(**request):
        prompt, content = request["contents"].split("\nCONTENT:\n", 1)
        requests.append((prompt, content))
        assert len(content) <= CHUNK_CHARS
        return SimpleNamespace(text="final concise summary" if "120 words" in prompt else ("e" * 29 + " ") * 80)

    source = " ".join(f"SECTION_{i:03d} " + "detail " * 800 for i in range(100))
    client = Mock()
    client.models.generate_content.side_effect = reply
    with caplog.at_level(logging.INFO, logger="assessment"):
        result = summarize_text(source, client, "test-model")
    assert 0 < len(result.split()) <= 120
    mapped = [content for prompt, content in requests if "80 words" in prompt]
    assert all(any(f"SECTION_{i:03d}" in content for content in mapped) for i in range(100))
    reduced = [content for prompt, content in requests if "60 words" in prompt]
    assert len(reduced) > 1
    assert sum('"event": "summary_reduced"' in record.message for record in caplog.records) >= 2


def test_nested_hidden_elements_are_removed_without_losing_visible_article():
    html = """<main><h1>Visible article</h1><p>Team costs MYR 35.</p>
    <div style="display: none"><span style="color: red">Hidden promotion</span></div>
    <div style="visibility: hidden"><p style="font-weight: bold">Hidden policy</p></div></main>"""
    text = extract_text(html)
    assert "Team costs MYR 35" in text
    assert "Hidden" not in text


def test_forced_render_rejects_a_page_that_remains_a_loading_shell(fixture_site):
    from part2.scraper import scrape_page

    with pytest.raises(ValueError, match="readable"):
        scrape_page(fixture_site + "/loading.html", render=True)


@pytest.mark.parametrize("reply", [None, "", "   "])
def test_blocked_or_empty_model_summary_reports_a_clear_failure(reply):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from part2.scraper import summarize_text

    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(text=reply)
    with pytest.raises(RuntimeError, match="no summary"):
        summarize_text("Team costs MYR 35.", client, "test-model")


def test_oversized_download_is_rejected_and_connection_is_closed(monkeypatch):
    from unittest.mock import Mock
    import requests
    from part2.scraper import MAX_HTML_BYTES, scrape_page

    response = Mock()
    response.headers = {"Content-Type": "text/html"}
    response.iter_content.return_value = [b"x" * MAX_HTML_BYTES, b"x"]
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(requests, "get", Mock(return_value=response))
    with pytest.raises(ValueError, match="2 MiB"):
        scrape_page("https://example.test/article")
    response.__exit__.assert_called_once()


def test_download_timeout_reports_a_clear_retryable_error(monkeypatch):
    from unittest.mock import Mock
    import requests
    from part2.scraper import scrape_page

    monkeypatch.setattr(requests, "get", Mock(side_effect=requests.Timeout("simulated timeout")))
    with pytest.raises(RuntimeError, match="network.*try later"):
        scrape_page("https://example.test/article")


@pytest.mark.parametrize("url", ["not a URL", "file:///article.html", "ftp://example.test/article", "https://"])
def test_invalid_url_is_rejected_before_any_download(url, monkeypatch):
    from unittest.mock import Mock
    import requests
    from part2.scraper import scrape_page

    download = Mock()
    monkeypatch.setattr(requests, "get", download)
    with pytest.raises(ValueError, match="http"):
        scrape_page(url)
    download.assert_not_called()


@pytest.mark.parametrize("html", ["", "<html><body></body></html>", "<main><script>ignored()</script></main>"])
def test_empty_extracted_page_is_rejected_before_model_call(html):
    from unittest.mock import Mock
    from part2.scraper import summarize_text

    client = Mock()
    with pytest.raises(ValueError, match="No readable"):
        summarize_text(extract_text(html), client, "test-model")
    client.models.generate_content.assert_not_called()
