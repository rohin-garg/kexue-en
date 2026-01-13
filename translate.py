import os
import re
import time
from typing import Any
from dotenv import load_dotenv
from exa_py import Exa
from firecrawl import FirecrawlApp
import requests
import json

load_dotenv()
exa = Exa(api_key = os.getenv("EXA_API_KEY"))
firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

PROMPT = \
"""
    Can you translate this to English? 

    You MUST output ONLY the translated blog post body content — the article itself. EXCLUDE ALL non-article website chrome and boilerplate, including (but not limited to):
    - Any site header / top nav / menu / search UI
    - Sidebars (categories, new posts, recent comments, login, archive lists, etc.)
    - Footer content, copyright blocks, “welcome” text, site slogans
    - Any “code / download / content_copy / expand_less” UI fragments or widgets
    - Any comment section and comment counts
    - Any subscription widgets or RSS links (unless they are inside the article body itself)
    - Any “related posts” / “recommended posts” modules


    Make sure to preserve all the math exactly. Output only raw HTML. Do not use Markdown, code fences/code blocks, or explanations. Please preserve all of the original links, math, and actual blogpost content.

    Preserve all original links, math, formatting, and blog content.
    This must be a one-to-one translation, not a summary or explanation.
    NEVER skip, simplify, or omit any formula or content-relevant text.

    Assume MathJax v3 is used.

    Always include a MathJax configuration block BEFORE loading MathJax that:

    * Enables `$...$` and `\\(...\\)` for inline math
    * Enables `$$...$$` and `\\[...\\]` for display math
    * Loads AMS packages (for equation numbering, `\\label`, `\\ref`, `\\eqref`, align, etc.)
    * Enables equation numbering / labels / references by setting `tex.tags` to `'ams'` (or `'all'`)

    IMPORTANT: Do not nest display math wrappers.

    * For display equations, use exactly ONE display wrapper.
    * If using AMS environments like `equation`, `align`, `gather`, etc., do NOT wrap them inside `$$...$$` or `\\[...\\]`.
    * If you are not using an AMS environment, then wrap the display equation using `$$...$$` or `\\[...\\]`.

    In other words:

    * Use `$$ ... $$` / `\\[ ... \\]` for plain display math (no `\begin{equation}` / `\begin{align}` inside).
    * Use `\\begin{equation}...\\end{equation}` or `\\begin{align}...\\end{align}` directly (not inside `$$` or `\\[ \\]`) when you need numbering/labels.

    Ensure all `\\label{...}`, `\\ref{...}`, and `\\eqref{...}` in the original content remain unchanged and resolve correctly under MathJax.
    """

# MODEL = "xiaomi/mimo-v2-flash:free"
# MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"
MODEL = "google/gemini-3-flash-preview"

CSS_STYLES = \
    """
    <style type="text/css">

    body {
    margin: 48px auto;
    max-width: 68ch;              /* character-based width reads better */
    padding: 0 16px;

    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 18px;
    line-height: 1.65;
    color: #333;
    background: #fafafa;
    }

    h1, h2, h3, h4 {
    line-height: 1.25;
    margin-top: 2.2em;
    margin-bottom: 0.6em;
    font-weight: 600;
    }

    h1 {
    font-size: 2.1em;
    margin-top: 0;
    }

    h2 {
    font-size: 1.6em;
    border-bottom: 1px solid #e5e5e5;
    padding-bottom: 0.3em;
    }

    h3 {
    font-size: 1.25em;
    }

    h4 {
    font-size: 1.05em;
    color: #555;
    }

    /* Paragraphs and lists */
    p {
    margin: 1em 0;
    }

    ul, ol {
    margin: 1em 0 1em 1.5em;
    }

    li {
    margin: 0.4em 0;
    }

    a {
    color: #005fcc;
    text-decoration: none;
    }

    a:hover {
    text-decoration: underline;
    }

    code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.95em;
    background: #f2f2f2;
    padding: 0.15em 0.35em;
    border-radius: 4px;
    }

    pre {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.9em;
    background: #f5f5f5;
    padding: 1em 1.2em;
    overflow-x: auto;
    border-radius: 6px;
    line-height: 1.45;
    }

    pre code {
    background: none;
    padding: 0;
    }

    blockquote {
    margin: 1.5em 0;
    padding-left: 1em;
    border-left: 4px solid #ddd;
    color: #555;
    }

    hr {
    border: none;
    border-top: 1px solid #e0e0e0;
    margin: 3em 0;
    }

    table {
    border-collapse: collapse;
    margin: 1.5em 0;
    width: 100%;
    font-size: 0.95em;
    }

    th, td {
    padding: 0.5em 0.7em;
    border-bottom: 1px solid #e5e5e5;
    text-align: left;
    }

    th {
    font-weight: 600;
    }

    img {
    max-width: 100%;
    display: block;
    margin: 1.5em auto;
    }

    small {
    color: #666;
    }

    mjx-container {
    margin: 1em 0;
    }

    ::selection {
    background: #cce2ff;
    }

    </style>
    """

def get_translation(url: str) -> str:
    result = exa.get_contents(
        [url],
        text = True
    )

    result = result.results[0].text
    print("=== DONE GETTING CONTENT ===")
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        },
        data=json.dumps({
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": result + "\n\n" + PROMPT
                }
            ],
            "reasoning": {
                "effort": "none"
            }
        })
    )
    print("=== DONE GETTING TRANSLATION ===")

    result = response.json()["choices"][0]["message"]["content"]
    return result

def save_translation(url: str, path = 'translations'):
    result = get_translation(url)
    full_html = CSS_STYLES + "\n\n" + result

    with open(f"{path}/translation_{url.split('/')[-1]}.html", "w") as f:
        f.write(full_html)

# ============== Caching Infrastructure ==============

CACHE_DIR = "cache"
RAW_DIR = f"{CACHE_DIR}/raw"

def ensure_cache_dirs():
    """Create cache directories if they don't exist."""
    os.makedirs(RAW_DIR, exist_ok=True)

def get_article_id(url: str) -> str:
    """Extract article ID from URL like https://kexue.fm/archives/11033"""
    return url.rstrip('/').split('/')[-1]

def discover_all_urls() -> list[dict]:
    """Discover all kexue.fm article URLs by crawling content.html.

    Returns a list of dicts with 'url', 'id', and 'year' keys.
    """
    print("Fetching content.html via Exa...")
    result = exa.get_contents(
        ["https://kexue.fm/content.html"],
        text=True
    )
    content = result.results[0].text

    # Save raw content.html for debugging
    ensure_cache_dirs()
    with open(f"{CACHE_DIR}/content_index.txt", 'w') as f:
        f.write(content)
    print(f"Saved content index to {CACHE_DIR}/content_index.txt")

    # Parse the content - look for patterns like "2015年" followed by article links
    # The content.html has year headers followed by article lists
    lines = content.split('\n')

    articles = []
    current_year = None

    for line in lines:
        # Check for year markers (e.g., "2015年", "2024年")
        year_match = re.search(r'(\d{4})年', line)
        if year_match:
            current_year = int(year_match.group(1))

        # Look for archive URLs
        url_matches = re.findall(r'/archives/(\d+)', line)
        for article_id in url_matches:
            articles.append({
                'id': article_id,
                'url': f"https://kexue.fm/archives/{article_id}",
                'year': current_year
            })

    # Deduplicate by article ID
    seen_ids = set()
    unique_articles = []
    for article in articles:
        if article['id'] not in seen_ids:
            seen_ids.add(article['id'])
            unique_articles.append(article)

    print(f"Found {len(unique_articles)} unique articles")
    return unique_articles

def filter_urls_by_year(articles: list[dict], min_year: int = 2015) -> list[dict]:
    """Filter articles to only include posts from min_year onwards."""
    filtered = [a for a in articles if a['year'] is None or a['year'] >= min_year]
    print(f"Filtered to {len(filtered)} articles from {min_year} onwards")
    return filtered

def cache_content(url: str) -> dict:
    """Fetch and cache content for a single URL."""
    article_id = get_article_id(url)
    cache_path = f"{RAW_DIR}/{article_id}.txt"

    # Skip if already cached
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            content = f.read()
        return {"url": url, "id": article_id, "cached": True, "chars": len(content)}

    # Fetch via Exa
    result = exa.get_contents([url], text=True)
    content = result.results[0].text

    # Save to cache
    with open(cache_path, 'w') as f:
        f.write(content)

    return {"url": url, "id": article_id, "cached": False, "chars": len(content)}

def cache_all_content(articles: list[dict]) -> list[dict]:
    """Cache content for all article URLs."""
    ensure_cache_dirs()
    results = []

    for i, article in enumerate(articles):
        url = article['url']
        print(f"[{i+1}/{len(articles)}] Caching {url}")
        try:
            result = cache_content(url)
            result['year'] = article.get('year')
            results.append(result)
        except Exception as e:
            print(f"  Error: {e}")
            results.append({"url": url, "id": article['id'], "error": str(e)})

    # Save metadata
    with open(f"{CACHE_DIR}/metadata.json", 'w') as f:
        json.dump(results, f, indent=2)

    return results

# ============== Firecrawl Fallback ==============

def cache_content_firecrawl(url: str) -> dict:
    """Fetch and cache content using Firecrawl (fallback for Exa failures)."""
    article_id = get_article_id(url)
    cache_path = f"{RAW_DIR}/{article_id}.txt"

    # Skip if already cached
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            content = f.read()
        return {"url": url, "id": article_id, "cached": True, "chars": len(content), "source": "existing"}

    # Fetch via Firecrawl
    result = firecrawl.scrape(url, formats=['markdown'])

    # Extract text content (result is a Pydantic Document model)
    content = result.markdown if result.markdown else ''
    if not content:
        raise ValueError("Firecrawl returned no markdown content")

    # Save to cache
    with open(cache_path, 'w') as f:
        f.write(content)

    return {"url": url, "id": article_id, "cached": False, "chars": len(content), "source": "firecrawl"}

def retry_failed_with_firecrawl(rate_limit_delay: float = 6.0):
    """Retry all failed articles using Firecrawl.

    Args:
        rate_limit_delay: Seconds to wait between requests (default 6s for ~10 req/min)
    """
    ensure_cache_dirs()

    # Load metadata to find failed articles
    metadata_path = f"{CACHE_DIR}/metadata.json"
    if not os.path.exists(metadata_path):
        print("No metadata.json found. Run 'python translate.py cache' first.")
        return []

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    # Find failed articles (check both original failures and Firecrawl failures)
    # Also check if file exists in cache (skip already cached)
    failed = []
    for item in metadata:
        if 'error' in item:
            article_id = item.get('id', item['url'].split('/')[-1])
            cache_path = f"{RAW_DIR}/{article_id}.txt"
            if not os.path.exists(cache_path):
                failed.append(item)

    print(f"Found {len(failed)} uncached articles to retry with Firecrawl")
    print(f"Rate limit delay: {rate_limit_delay}s between requests")

    results = []
    for i, item in enumerate(failed):
        url = item['url']
        print(f"[{i+1}/{len(failed)}] Retrying {url}")
        try:
            result = cache_content_firecrawl(url)
            results.append(result)
            if result.get('source') == 'firecrawl':
                print(f"  SUCCESS: {result['chars']} chars")
            else:
                print(f"  SKIPPED: already cached")
        except Exception as e:
            print(f"  FAILED: {e}")
            results.append({"url": url, "id": item.get('id', ''), "error": str(e), "source": "firecrawl"})

        # Rate limiting - wait between requests
        if i < len(failed) - 1:  # Don't wait after last request
            time.sleep(rate_limit_delay)

    # Save Firecrawl results
    with open(f"{CACHE_DIR}/firecrawl_results.json", 'w') as f:
        json.dump(results, f, indent=2)

    # Update metadata with successes
    success_count = len([r for r in results if 'error' not in r and r.get('source') == 'firecrawl'])
    print(f"\nFirecrawl recovered {success_count}/{len(failed)} articles")

    # Recalculate totals
    token_stats = calculate_total_tokens()
    print(f"New total: {token_stats['file_count']} articles, {token_stats['total_chars']:,} chars")

    return results

# ============== Token & Cost Estimation ==============

def estimate_tokens(chars: int) -> int:
    """Estimate token count. Uses 1.5 chars/token for Chinese-heavy content."""
    return int(chars / 1.5)

def calculate_total_tokens() -> dict:
    """Calculate total tokens across all cached content."""
    total_chars = 0
    file_count = 0

    for filename in os.listdir(RAW_DIR):
        if filename.endswith('.txt'):
            with open(f"{RAW_DIR}/{filename}", 'r') as f:
                total_chars += len(f.read())
            file_count += 1

    total_tokens = estimate_tokens(total_chars)
    return {
        "file_count": file_count,
        "total_chars": total_chars,
        "estimated_tokens": total_tokens
    }

def estimate_cost(input_tokens: int, output_tokens: int = None) -> dict:
    """Estimate translation cost with Gemini 3 Flash via OpenRouter.

    Pricing:
    - Input: $0.50 per 1M tokens
    - Output: $3.00 per 1M tokens
    """
    if output_tokens is None:
        output_tokens = input_tokens  # Assume ~1:1 translation ratio

    input_cost = input_tokens * 0.0000005   # $0.50/M
    output_cost = output_tokens * 0.000003  # $3.00/M
    total_cost = input_cost + output_cost

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": round(input_cost, 4),
        "output_cost_usd": round(output_cost, 4),
        "total_cost_usd": round(total_cost, 4)
    }

def run_cache_and_estimate():
    """Main function to discover URLs, cache content, and estimate costs."""
    # Step 1: Discover URLs
    print("=" * 50)
    print("STEP 1: Discovering article URLs")
    print("=" * 50)
    all_articles = discover_all_urls()

    # Step 2: Filter to 2015+
    print("\n" + "=" * 50)
    print("STEP 2: Filtering to 2015 onwards")
    print("=" * 50)
    filtered_articles = filter_urls_by_year(all_articles, min_year=2015)

    # Save URL list
    with open(f"{CACHE_DIR}/urls.json", 'w') as f:
        json.dump(filtered_articles, f, indent=2)
    print(f"Saved URL list to {CACHE_DIR}/urls.json")

    # Step 3: Cache all content
    print("\n" + "=" * 50)
    print("STEP 3: Caching content")
    print("=" * 50)
    cache_results = cache_all_content(filtered_articles)

    # Step 4: Calculate tokens and cost
    print("\n" + "=" * 50)
    print("STEP 4: Token & Cost Estimation")
    print("=" * 50)
    token_stats = calculate_total_tokens()
    cost_estimate = estimate_cost(token_stats['estimated_tokens'])

    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total articles: {token_stats['file_count']}")
    print(f"Total characters: {token_stats['total_chars']:,}")
    print(f"Estimated tokens: {token_stats['estimated_tokens']:,}")
    print(f"\nCost estimate (Gemini 3 Flash via OpenRouter):")
    print(f"  Input cost:  ${cost_estimate['input_cost_usd']:.2f}")
    print(f"  Output cost: ${cost_estimate['output_cost_usd']:.2f}")
    print(f"  Total cost:  ${cost_estimate['total_cost_usd']:.2f}")
    print(f"\n(Assumes 1:1 input/output ratio for translation)")

    return {
        "articles": len(filtered_articles),
        "token_stats": token_stats,
        "cost_estimate": cost_estimate
    }

# ============== Post-Processing ==============

# Base URL for translated articles - change this when you have a domain
# Examples:
#   "https://kexue-en.com" -> links become "https://kexue-en.com/archives/11033"
#   "/translations" -> links become "/translations/translation_11033.html"
#   "" -> links stay as relative "translation_11033.html"
TRANSLATED_BASE_URL = ""  # Empty = relative links like "translation_XXXX.html"

def rewrite_internal_links(html: str) -> str:
    """Rewrite links to other kexue.fm articles to point to translated versions.

    Converts: https://kexue.fm/archives/XXXX
    To: {TRANSLATED_BASE_URL}/translation_XXXX.html (or configured format)
    """
    def replace_link(match):
        article_id = match.group(1)
        if TRANSLATED_BASE_URL:
            # Use configured base URL
            if TRANSLATED_BASE_URL.startswith("http"):
                # Full domain: https://kexue-en.com/archives/XXXX
                return f'{TRANSLATED_BASE_URL}/archives/{article_id}'
            else:
                # Relative path: /translations/translation_XXXX.html
                return f'{TRANSLATED_BASE_URL}/translation_{article_id}.html'
        else:
            # Default: relative link to translation file
            return f'translation_{article_id}.html'

    # Match href="https://kexue.fm/archives/XXXX" (with or without trailing slash)
    pattern = r'href="https?://kexue\.fm/archives/(\d+)/?\"'
    html = re.sub(pattern, lambda m: f'href="{replace_link(m)}"', html)

    return html

def inject_author_date_from_cache(html: str, article_id: str) -> str:
    """Inject author/date line if missing, using date from raw cache."""
    from datetime import datetime

    # Check if author line already exists
    if re.search(r'<p>By (?:苏剑林|Su Jianlin)', html):
        return html

    # Try to get date from raw cache
    cache_path = f"{RAW_DIR}/{article_id}.txt"
    if not os.path.exists(cache_path):
        return html

    with open(cache_path, 'r') as f:
        raw_content = f.read()

    # Look for Chinese citation pattern: 苏剑林. (Jan. 06, 2022) or 苏剑林. (2022-01-06)
    date_str = None

    # Try abbreviated month format
    match = re.search(r'苏剑林\.\s*\(([A-Z][a-z]{2,3})\.?\s*(\d{1,2}),?\s*(\d{4})\)', raw_content)
    if match:
        try:
            date = datetime.strptime(f"{match.group(1)[:3]} {match.group(2)} {match.group(3)}", "%b %d %Y")
            date_str = date.strftime("%B %d, %Y")
        except ValueError:
            pass

    # Try ISO format
    if not date_str:
        match = re.search(r'苏剑林\.\s*\((\d{4})-(\d{2})-(\d{2})\)', raw_content)
        if match:
            try:
                date = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                date_str = date.strftime("%B %d, %Y")
            except ValueError:
                pass

    if not date_str:
        return html

    # Inject author line after </h1>
    author_line = f'\n\n    <p>By 苏剑林 | {date_str}</p>\n'
    html = re.sub(r'(</h1>)', r'\1' + author_line, html, count=1)

    return html


def standardize_author_date(html: str) -> str:
    """Standardize the author/date line to a consistent format.

    Converts various formats to: <p>By 苏剑林 | Month DD, YYYY</p>
    """
    from datetime import datetime

    # Author name variations (plain text or linked, with optional English name in parens)
    author_pattern = r'(?:苏剑林(?: \(Su Jianlin\))?|Su Jianlin|Jianlin Su|<a[^>]*>(?:Su Jianlin|Jianlin Su|苏剑林)</a>)'
    # Whitespace that may include newlines
    ws = r'[\s\n]*'

    # Pattern to match various author/date formats
    patterns = [
        # ISO date with optional reader count (possibly multiline)
        (rf'<p>{ws}By {ws}{author_pattern} {ws}\| {ws}(\d{{4}})-(\d{{2}})-(\d{{2}})(?:{ws}\|[^<]*)?\s*</p>',
         lambda m: f'<p>By 苏剑林 | {datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).strftime("%B %d, %Y")}</p>'),

        # Full month with optional reader count (possibly multiline)
        (rf'<p>{ws}By {ws}{author_pattern} {ws}\| {ws}([A-Z][a-z]+ \d{{1,2}}, \d{{4}})(?:{ws}\|[^<]*)?\s*</p>',
         lambda m: f'<p>By 苏剑林 | {m.group(1)}</p>'),

        # Abbreviated month with optional reader count (possibly multiline)
        (rf'<p>{ws}By {ws}{author_pattern} {ws}\| {ws}([A-Z][a-z]{{2,3}})\.? (\d{{1,2}}), (\d{{4}})(?:{ws}\|[^<]*)?\s*</p>',
         lambda m: f'<p>By 苏剑林 | {datetime.strptime(f"{m.group(1)[:3]} {m.group(2)} {m.group(3)}", "%b %d %Y").strftime("%B %d, %Y")}</p>'),

        # "Published" format: "By X | Published Jan 20, 2019"
        (rf'<p>{ws}By {ws}{author_pattern} {ws}\| {ws}Published {ws}([A-Z][a-z]{{2,3}})\.? (\d{{1,2}}), (\d{{4}})\s*</p>',
         lambda m: f'<p>By 苏剑林 | {datetime.strptime(f"{m.group(1)[:3]} {m.group(2)} {m.group(3)}", "%b %d %Y").strftime("%B %d, %Y")}</p>'),
    ]

    for pattern, replacement in patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                new_line = replacement(match)
                html = re.sub(pattern, new_line, html, count=1, flags=re.DOTALL)
                break
            except (ValueError, IndexError) as e:
                continue

    return html


def remove_translated_citation(html: str) -> str:
    """Remove the translated citation block from the original Chinese page.

    The original pages have a citation section at the end that gets translated.
    This includes things like:
    - "Reprinting is allowed as long as..."
    - "If you need to cite this article..."
    - BibTeX code blocks
    """
    # Remove "Reprinting is allowed..." paragraph and link
    # Pattern: <p><em><strong>Reprinting...:</strong>...<a href="...">...</a></em></p>
    html = re.sub(
        r'<p><em><strong>Reprinting[^<]*</strong>[^<]*<a[^>]*>[^<]*</a></em></p>\s*',
        '',
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Remove "If you need to cite..." paragraph
    html = re.sub(
        r'<p><strong>If you need to cite[^<]*</strong></p>\s*',
        '',
        html,
        flags=re.IGNORECASE
    )

    # Remove the citation paragraph that follows (author, date, title, url)
    html = re.sub(
        r'<p>Su Jianlin\.\s*\([^)]+\)\.\s*"[^"]+"\.\s*\[Blog post\]\.\s*Retrieved from[^<]*<a[^>]*>[^<]*</a></p>\s*',
        '',
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Remove BibTeX code blocks
    html = re.sub(
        r'<pre><code>@online\{kexuefm-\d+,.*?</code></pre>\s*',
        '',
        html,
        flags=re.DOTALL
    )

    return html


def postprocess_html(html: str, article_id: str) -> str:
    """Post-process translated HTML to add source link and citation.

    1. Removes translated citation block from original page
    2. Rewrites internal kexue.fm links to translated versions
    3. Ensures title links to original article
    4. Adds citation footer
    """
    original_url = f"https://kexue.fm/archives/{article_id}"

    # Step 0: Remove translated citation block from original page
    html = remove_translated_citation(html)

    # Step 0.5: Inject author/date line if missing (from cache)
    html = inject_author_date_from_cache(html, article_id)

    # Step 0.6: Standardize author/date format
    html = standardize_author_date(html)

    # Step 1: Rewrite internal kexue.fm links to translated versions
    # (Do this BEFORE fixing the title link, so title stays pointing to original)
    html = rewrite_internal_links(html)

    # Step 2: Ensure <h1> title links to original (not translated)
    # Pattern: <h1>Title Text</h1> (without link)
    # Should become: <h1><a href="...">Title Text</a></h1>

    h1_pattern = r'<h1>([^<]+)</h1>'
    h1_match = re.search(h1_pattern, html)

    if h1_match:
        # Title exists but isn't linked - add link
        title_text = h1_match.group(1)
        # Escape backslashes for re.sub replacement (LaTeX math like \det would fail otherwise)
        escaped_title = title_text.replace('\\', '\\\\')
        linked_title = f'<h1><a href="{original_url}">{escaped_title}</a></h1>'
        html = re.sub(h1_pattern, linked_title, html, count=1)

    # Check if title is already linked but to wrong URL or missing
    h1_link_pattern = r'<h1><a href="([^"]*)">'
    h1_link_match = re.search(h1_link_pattern, html)

    if h1_link_match:
        current_url = h1_link_match.group(1)
        if original_url not in current_url:
            # Fix the URL
            html = re.sub(h1_link_pattern, f'<h1><a href="{original_url}">', html, count=1)

    # Step 3: Add citation footer (before closing </body> or at end)
    citation = f'''
<hr>
<footer style="margin-top: 3em; padding: 1.5em; background: #f5f5f5; border-radius: 8px; font-size: 0.9em; color: #555;">
    <p style="margin: 0 0 0.5em 0;"><strong>Citation</strong></p>
    <p style="margin: 0 0 0.5em 0;">
        This is a machine translation of the original Chinese article:<br>
        <a href="{original_url}" style="color: #005fcc;">{original_url}</a>
    </p>
    <p style="margin: 0 0 0.5em 0;">
        Original author: 苏剑林 (Su Jianlin)<br>
        Original publication: <a href="https://kexue.fm" style="color: #005fcc;">科学空间 (Scientific Spaces)</a>
    </p>
    <p style="margin: 0; font-style: italic;">
        Translated using Gemini 3 Flash. Please refer to the original for authoritative content.
    </p>
</footer>
'''

    # Check if citation already exists (avoid duplicates)
    if 'This is a machine translation' not in html:
        # Try to insert before </body>, otherwise append
        if '</body>' in html:
            html = html.replace('</body>', citation + '\n</body>')
        else:
            html = html + citation

    return html

def postprocess_translation_file(article_id: str, path='translations'):
    """Post-process an existing translation file."""
    filepath = f"{path}/translation_{article_id}.html"

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Translation file not found: {filepath}")

    with open(filepath, 'r') as f:
        html = f.read()

    html = postprocess_html(html, article_id)

    with open(filepath, 'w') as f:
        f.write(html)

    print(f"Post-processed: {filepath}")
    return filepath

def translate_from_cache(article_id: str, timeout: int = 300, max_retries: int = 2) -> str:
    """Translate an article from cached content.

    Args:
        article_id: The article ID to translate
        timeout: Request timeout in seconds (default 5 min)
        max_retries: Number of retries on failure
    """
    cache_path = f"{RAW_DIR}/{article_id}.txt"

    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"No cached content for article {article_id}")

    with open(cache_path, 'r') as f:
        content = f.read()

    print(f"Translating article {article_id} ({len(content)} chars)...")

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                },
                data=json.dumps({
                    "model": MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": content + "\n\n" + PROMPT
                        }
                    ],
                    "reasoning": {
                        "effort": "none"
                    }
                }),
                timeout=timeout
            )

            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"]
            return result

        except requests.exceptions.Timeout:
            last_error = f"Request timed out after {timeout}s"
            print(f"  Timeout on attempt {attempt + 1}/{max_retries + 1}")
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            print(f"  Request error on attempt {attempt + 1}/{max_retries + 1}: {e}")
        except (KeyError, IndexError) as e:
            last_error = f"Invalid API response: {e}"
            print(f"  Invalid response on attempt {attempt + 1}/{max_retries + 1}: {e}")

        if attempt < max_retries:
            time.sleep(5)  # Wait before retry

    raise Exception(f"Failed after {max_retries + 1} attempts: {last_error}")

def save_translation_from_cache(article_id: str, path='translations'):
    """Translate and save an article from cache."""
    result = translate_from_cache(article_id)
    full_html = CSS_STYLES + "\n\n" + result

    # Apply post-processing
    full_html = postprocess_html(full_html, article_id)

    os.makedirs(path, exist_ok=True)
    output_path = f"{path}/translation_{article_id}.html"
    with open(output_path, "w") as f:
        f.write(full_html)

    print(f"Saved translation to {output_path}")
    return output_path

def translate_all(path='translations', skip_existing=True):
    """Translate all cached articles.

    Args:
        path: Output directory for translations
        skip_existing: If True, skip articles that already have translations
    """
    ensure_cache_dirs()
    os.makedirs(path, exist_ok=True)

    # Get all cached article IDs
    cached_ids = []
    for filename in os.listdir(RAW_DIR):
        if filename.endswith('.txt'):
            article_id = filename[:-4]  # Remove .txt
            cached_ids.append(article_id)

    cached_ids.sort(key=lambda x: int(x), reverse=True)  # Newest first
    print(f"Found {len(cached_ids)} cached articles")

    # Filter out existing translations if skip_existing
    if skip_existing:
        to_translate = []
        for article_id in cached_ids:
            output_path = f"{path}/translation_{article_id}.html"
            if not os.path.exists(output_path):
                to_translate.append(article_id)
        print(f"Skipping {len(cached_ids) - len(to_translate)} existing translations")
        print(f"Will translate {len(to_translate)} articles")
    else:
        to_translate = cached_ids

    if not to_translate:
        print("No articles to translate!")
        return []

    # Track results
    results = {"success": [], "failed": []}

    for i, article_id in enumerate(to_translate):
        print(f"[{i+1}/{len(to_translate)}] Translating article {article_id}...")
        try:
            save_translation_from_cache(article_id, path)
            results["success"].append(article_id)
        except Exception as e:
            print(f"  FAILED: {e}")
            results["failed"].append({"id": article_id, "error": str(e)})

        # Save progress periodically
        if (i + 1) % 10 == 0:
            with open(f"{CACHE_DIR}/translation_progress.json", 'w') as f:
                json.dump(results, f, indent=2)
            print(f"  Progress saved: {len(results['success'])} succeeded, {len(results['failed'])} failed")

    # Final save
    with open(f"{CACHE_DIR}/translation_progress.json", 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 50)
    print("TRANSLATION COMPLETE")
    print("=" * 50)
    print(f"Succeeded: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")
    if results['failed']:
        print(f"Failed articles: {[x['id'] for x in results['failed']]}")

    return results


def retry_failed_translations(path='translations'):
    """Retry all failed translations from the progress file."""
    progress_file = f"{CACHE_DIR}/translation_progress.json"

    if not os.path.exists(progress_file):
        print("No progress file found!")
        return

    with open(progress_file, 'r') as f:
        progress = json.load(f)

    failed = progress.get('failed', [])
    if not failed:
        print("No failed translations to retry!")
        return

    # Extract article IDs from failed list
    failed_ids = [x['id'] if isinstance(x, dict) else x for x in failed]
    print(f"Retrying {len(failed_ids)} failed translations: {failed_ids}")

    retried_success = []
    retried_failed = []

    for i, article_id in enumerate(failed_ids):
        print(f"[{i+1}/{len(failed_ids)}] Retrying article {article_id}...")
        try:
            save_translation_from_cache(article_id, path)
            retried_success.append(article_id)
            print(f"  SUCCESS!")
        except Exception as e:
            print(f"  FAILED again: {e}")
            retried_failed.append({"id": article_id, "error": str(e)})

    # Update progress file
    progress['success'].extend(retried_success)
    progress['failed'] = retried_failed

    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)

    print("\n" + "=" * 50)
    print("RETRY COMPLETE")
    print("=" * 50)
    print(f"Newly succeeded: {len(retried_success)}")
    print(f"Still failed: {len(retried_failed)}")
    if retried_failed:
        print(f"Still failed articles: {[x['id'] for x in retried_failed]}")

    return {"success": retried_success, "failed": retried_failed}


def postprocess_all(path='translations'):
    """Re-run postprocessing on all translation files."""
    import glob

    files = glob.glob(f"{path}/translation_*.html")
    print(f"Found {len(files)} translation files to postprocess")

    for i, filepath in enumerate(files):
        # Extract article ID from filename
        article_id = filepath.split('_')[-1].replace('.html', '')

        if (i + 1) % 50 == 0:
            print(f"[{i+1}/{len(files)}] Processing...")

        try:
            with open(filepath, 'r') as f:
                html = f.read()

            html = postprocess_html(html, article_id)

            with open(filepath, 'w') as f:
                f.write(html)
        except Exception as e:
            print(f"  Error on {article_id}: {e}")

    print(f"Done! Postprocessed {len(files)} files.")


def add_new_post(url_or_id: str, force: bool = False):
    """Add a new blog post: fetch, cache, translate, and update index."""
    import subprocess
    import sys

    # Extract article ID from URL or use directly
    if url_or_id.startswith('http'):
        article_id = url_or_id.rstrip('/').split('/')[-1]
        url = url_or_id
    else:
        article_id = url_or_id
        url = f"https://kexue.fm/archives/{article_id}"

    print(f"Adding new post: {url}")
    print(f"Article ID: {article_id}")
    print()

    # Step 1: Check if already translated
    translation_path = f"translations/translation_{article_id}.html"
    if os.path.exists(translation_path) and not force:
        print(f"Translation already exists: {translation_path}")
        print("Use --force to re-translate")
        return

    # Step 2: Cache content (fetch if needed)
    print("Step 1/4: Fetching content...")
    cache_path = f"{RAW_DIR}/{article_id}.txt"
    if os.path.exists(cache_path) and not force:
        print(f"  Already cached: {cache_path}")
    else:
        try:
            result = cache_content(url)
            print(f"  Cached {result['chars']} chars")
        except Exception as e:
            print(f"  Exa failed: {e}")
            print("  Trying Firecrawl...")
            try:
                result = cache_content_firecrawl(url)
                print(f"  Cached {result['chars']} chars via Firecrawl")
            except Exception as e2:
                print(f"  Firecrawl also failed: {e2}")
                return

    # Step 3: Translate
    print("Step 2/4: Translating...")
    try:
        save_translation_from_cache(article_id)
        print(f"  Saved: {translation_path}")
    except Exception as e:
        print(f"  Translation failed: {e}")
        return

    # Step 4: Clean up articles (remove quirks like hashtag links, etc.)
    print("Step 3/5: Cleaning up articles...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([sys.executable, os.path.join(script_dir, "cleanup_articles.py")], check=True)
    print("  Cleaned up translations")

    # Step 5: Regenerate index
    print("Step 4/5: Updating index...")
    subprocess.run([sys.executable, os.path.join(script_dir, "generate_contents.py")], check=True)
    print("  Updated index.html")

    # Step 6: Regenerate search index
    print("Step 5/5: Updating search index...")
    subprocess.run([sys.executable, os.path.join(script_dir, "build_search_index.py")], check=True)
    print("  Updated search-index.js")

    print()
    print("Done! New post added successfully.")
    print(f"  Translation: {translation_path}")
    print(f"  Original: {url}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "add":
        # Add a new post
        if len(sys.argv) < 3:
            print("Usage: python translate.py add <url_or_id> [--force]")
            print("Example: python translate.py add https://kexue.fm/archives/12345")
            print("Example: python translate.py add 12345")
            sys.exit(1)
        force = "--force" in sys.argv
        add_new_post(sys.argv[2], force=force)
    elif len(sys.argv) > 1 and sys.argv[1] == "cache":
        # Run caching and estimation
        run_cache_and_estimate()
    elif len(sys.argv) > 1 and sys.argv[1] == "firecrawl":
        # Retry failed articles with Firecrawl
        retry_failed_with_firecrawl()
    elif len(sys.argv) > 1 and sys.argv[1] == "translate" and len(sys.argv) > 2:
        # Translate a specific cached article
        article_id = sys.argv[2]
        save_translation_from_cache(article_id)
    elif len(sys.argv) > 1 and sys.argv[1] == "postprocess" and len(sys.argv) > 2:
        # Post-process existing translation file(s)
        for article_id in sys.argv[2:]:
            postprocess_translation_file(article_id)
    elif len(sys.argv) > 1 and sys.argv[1] == "translate-all":
        # Translate all cached articles
        translate_all()
    elif len(sys.argv) > 1 and sys.argv[1] == "retry-failed":
        # Retry failed translations
        retry_failed_translations()
    elif len(sys.argv) > 1 and sys.argv[1] == "postprocess-all":
        # Re-run postprocessing on all files
        postprocess_all()
    else:
        print("Usage: python translate.py <command> [args]")
        print()
        print("Commands:")
        print("  add <url_or_id> [--force]  Add and translate a new article")
        print("  cache                      Run caching and estimation")
        print("  firecrawl                  Retry failed articles with Firecrawl")
        print("  translate <id>             Translate a specific cached article")
        print("  translate-all              Translate all cached articles")
        print("  retry-failed               Retry failed translations")
        print("  postprocess <id>...        Post-process specific translation(s)")
        print("  postprocess-all            Re-run postprocessing on all files")
        sys.exit(1)