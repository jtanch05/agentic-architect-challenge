# Website scraping and concise summaries

## Hypothetical starting problem

The assessment did not include a broken script. For this example, assume the original script downloads a page once, combines all paragraph text and sends it to the model in one request.

This approach has four main problems:

- A normal HTTP request does not run JavaScript, so it may download an empty page shell instead of the article.
- Extracting only paragraphs can miss headings and tables while still including menus and advertisements.
- Sending all content in one request can cost more, take longer, exceed the model input limit, or miss important details.
- Telling the model to be concise does not guarantee a maximum summary length.

## Improved scraping

`scraper.py` uses connection and download timeouts and limits HTML to 2 MiB. BeautifulSoup removes common menus, scripts and hidden elements, then searches for the main article content, including tables.

If the extracted text is shorter than 200 characters, Playwright opens the page in a browser and runs its JavaScript. It waits up to five seconds for content after navigation. The `--render` option forces this step when the downloaded page contains placeholder text but not the article. HTTP errors are shown clearly.

The scraper supports common HTML pages, but it cannot handle every site. It does not support external CSS visibility rules, iframes, infinite scrolling, login pages, paywalls or CAPTCHA. The 2 MiB limit applies to the resulting HTML, not all files downloaded by the browser. Only scrape pages you are allowed to access.

## Handling long content

The script splits text into chunks of up to 6,000 characters. Gemini creates short notes for each chunk. The script then groups and summarises those notes again until they fit into one 6,000-character input. It then creates the final summary. Each set of notes has word and character limits, so the content becomes shorter at every stage. Every accepted chunk is processed, including the end of the article.

The script accepts at most **100 source chunks**. It rejects a larger input before calling the model, so it must be split into separate articles. This limit and the 2 MiB HTML limit are prototype choices to control cost and processing time.

Repeated summarisation can remove useful details. Processing every chunk means every part of the article reaches the model, but it does not guarantee that every fact appears in the final summary.

## Keeping the summary concise

The final summary is limited to **120 words**. The script counts words by whitespace. The assessment does not specify a word count, so 120 words is a design choice.

If the first summary is too long, Gemini is asked once to shorten it. The code then applies a fixed word limit and keeps a complete sentence where possible. This final limit can remove details, so the logs record when it is used. A model output-token limit alone cannot guarantee a maximum word count.

## Run

From the repository root, after installing dependencies and configuring `.env`:

```powershell
python -m part2.scraper https://example.com
python -m part2.scraper https://example.com --render
python -m part2.scraper --html PATH_TO_FILE
```

Replace the example URL with a page you are allowed to scrape, or provide a local HTML file. Use `--render` when JavaScript content is missing from the downloaded HTML.

The summary is printed to standard output. Logs on standard error show the extraction method, chunk count, summarisation progress, model response time, final word count and whether the fixed word limit was used.

Each Gemini request has a 30-second timeout, with up to two attempts in total. Requests run one at a time. Articles near the chunk limit can need more than 100 model calls, including the repeated summarisation steps. This increases processing time and Gemini quota use. No performance benchmark was run.
