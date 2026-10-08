# Scraping and concise summarisation

## Hypothetical starting problem

No broken script was supplied. Assume a naive script fetches HTML with one HTTP request, joins every paragraph, and sends all text in one model request. This is an illustrative baseline, not a diagnosis of supplied code.

Its bottlenecks are:

- HTTP fetching does not execute JavaScript, so an application shell may contain no article.
- Paragraph-only scraping can miss headings, tables, and other content while including navigation and adverts.
- A single unbounded prompt increases latency/cost and can exceed context limits or lose information from long inputs.
- A prompt saying "be concise" is not an enforceable output limit.

## Implemented approach

`scraper.py` downloads HTML with connect/read timeouts and a 2 MiB limit. BeautifulSoup removes common navigation, script and hidden elements and prioritises main/article content, including tables. If static readable content is under 200 characters, Playwright renders the page and waits up to 5 seconds for content after navigation. `--render` forces rendering when a substantial shell masks missing article content. HTTP errors are reported rather than bypassed.

The extractor is intentionally general: it does not promise success for every website. External CSS visibility, iframes, infinite scrolling, authentication, paywalls and CAPTCHA are not handled. A browser renders scripts and makes subresource requests; the 2 MiB limit bounds the resulting HTML, not total browser network traffic. Use only pages you are permitted to scrape.

Long text is divided into chunks of at most 6,000 characters. Each source chunk becomes notes; notes are grouped and summarised repeatedly until the combined notes fit one 6,000-character content payload, then the final summary is generated. Intermediate notes have word/character caps so each reduction level shrinks. All accepted source chunks are processed, including the tail. This hierarchical map/reduce approach handles articles beyond the earlier 12-chunk limit without creating an oversized final content payload.

An absolute **100-source-chunk safety budget** remains: larger inputs are rejected before any model call and must be split into separate articles. This is a prototype cost/latency assumption, not a requirement from the employer. The 2 MiB HTML limit also remains. Summarisation can lose detail; more reduction levels increase that risk, and sending every chunk to a model does not prove that every fact survives in the final answer.

The final limit is **120 whitespace-separated words**, an explicit assessment assumption. An overlong output is shortened once by Gemini; a deterministic cap then enforces the bound and prefers a complete sentence when possible. A forced cap can omit details, so the logs report when it occurs. Output-token limits alone do not guarantee a word limit.

## Run

From the repository root with dependencies and `.env` configured:

```powershell
python -m part2.scraper https://example.com
python -m part2.scraper https://example.com --render
python -m part2.scraper --html PATH_TO_FILE
```

Replace the example URL with a permitted article, or provide your own local HTML file. Use `--render` when a substantial static shell masks JavaScript content.

Logs on stderr show extraction method, chunk count, reduction progress, model-call latency, final word count and whether the hard cap was applied. The summary is printed on stdout. Gemini has a 30-second per-attempt timeout and up to 2 total attempts. Requests run sequentially; near the safety limit, the job can require over 100 model calls including reductions, consuming more quota and taking substantially longer. No performance benchmark is claimed.
