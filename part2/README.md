# Website scraping and concise summaries

## Hypothetical starting problem

The assessment did not include a broken script. This example therefore assumes a starting script that downloads a page once, combines all paragraph text and sends it to the model in one request.

This approach has four main problems:

- A normal HTTP request does not run JavaScript, so it may retrieve the page structure without the article content.
- Extracting only paragraphs can miss headings and tables while still including menus and advertisements.
- Sending all content in one request can increase cost and response time, exceed the model's input limit or lead to missing details in the summary.
- Telling the model to be concise does not guarantee a maximum summary length.

## Improved scraping

`scraper.py` sets timeouts for connecting to and downloading a page, and limits the HTML to 2 MiB. BeautifulSoup removes common menus, scripts and hidden elements. It then looks for the main article content, including tables.

The code separates downloading from extraction. `download_html()` handles the HTTP request, size limit and network errors. `scrape_page()` chooses between extracting the downloaded HTML and rendering the page in a browser.

If the extracted text contains fewer than 200 characters, Playwright opens the page in a browser and runs its JavaScript. After navigation, it waits up to five seconds for content to appear. Use `--render` to request browser rendering explicitly, for example when the downloaded HTML contains substantial placeholder text but no article. HTTP errors are reported with clear messages.

The scraper supports common HTML pages, but it cannot handle every site. It does not support external CSS visibility rules, iframes, infinite scrolling, login pages, paywalls or CAPTCHA. The 2 MiB limit applies to the resulting HTML, not all files downloaded by the browser. Only scrape pages you are allowed to access.

## Handling long content

The script splits the text into chunks of up to 6,000 characters. Gemini creates short notes for each chunk. The script combines these notes and summarises them again as needed until they fit into one 6,000-character input. Gemini then produces the final summary. Word and character limits make the notes shorter at each stage. Every accepted chunk is processed, including the end of the article.

`summarize_text()` manages this sequence, while `reduce_notes()` handles the repeated summarisation of combined notes. Keeping these steps separate makes the main flow easier to follow.

The script accepts up to **100 source chunks**. Larger inputs are rejected before any model call and must be divided into smaller inputs. This limit and the 2 MiB HTML limit are prototype choices intended to control cost and processing time.

Repeated summarisation can remove useful details. Processing every chunk means every part of the article reaches the model, but it does not guarantee that every fact appears in the final summary.

## Keeping the summary concise

The final summary is limited to **120 words**. The script counts words by whitespace. The assessment does not specify a word count, so 120 words is a design choice.

If the first summary is too long, the script asks Gemini once to shorten it. The code then enforces the word limit, ending at a complete sentence where possible. This final cut can remove details, so the logs record when it is needed. Limiting the model's output tokens alone does not guarantee a maximum word count.

## Run

Complete the [local setup](../README.md#local-setup), then run these commands from the repository root. Activate the environment in each new terminal session:

```powershell
.\.venv\Scripts\Activate.ps1
python -m part2.scraper https://example.com
python -m part2.scraper https://example.com --render
python -m part2.scraper --html PATH_TO_FILE
```

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe -m part2.scraper https://example.com` instead. Add the same options shown above as needed.

Replace the example URL with a page you are allowed to scrape, or provide a local HTML file. Use `--render` when JavaScript content is missing from the downloaded HTML.

The summary is printed to standard output. Logs on standard error show the extraction method, chunk count, summarisation progress, model response time, final word count and whether the fixed word limit was used.

To save usage information separately, add `--usage-log summary-usage.log`. This optional local file records the estimated minimum number of model calls, flags estimates above ten calls and counts calls made by the application, including failed calls. Usage information stays out of the terminal. The option adds no usage limit and does not record page text or credentials. Automatic retries by the Gemini SDK can make additional HTTP requests. `.log` files are excluded from Git.

The local prototype limits input sizes and retry attempts. It does not automatically retry quota errors. Anyone using Gemini needs an API key with available quota. A future public service would also need authentication, limits on requests per user, controls on simultaneous requests and cost monitoring. API keys would remain on the server.

Each Gemini attempt has a 30-second timeout. Selected temporary HTTP errors allow up to two attempts. HTTP 429 is not retried automatically; check your usage and wait for the rate or quota limit to reset. The timeout applies to each attempt, rather than the whole article.

Requests run one at a time. Articles near the chunk limit can require more than 100 model calls because the notes may need several rounds of summarisation. This increases processing time and quota use. Processing capacity has not been measured with real Gemini requests.
