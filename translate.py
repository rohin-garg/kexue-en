import os
from typing import Any
from dotenv import load_dotenv
from exa_py import Exa
import requests
import json

load_dotenv()
exa = Exa(api_key = os.getenv("EXA_API_KEY"))

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

if __name__ == "__main__":
    url = "https://kexue.fm/archives/11033"
    save_translation(url)