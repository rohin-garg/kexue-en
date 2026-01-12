#!/usr/bin/env python3
"""Generate a contents page for all translated articles."""

import os
import re
from datetime import datetime
from pathlib import Path

def extract_info(filepath):
    """Extract title and date from a translation file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title from <h1><a href="...">TITLE</a></h1>
    title_match = re.search(r'<h1><a href="[^"]+">([^<]+)</a></h1>', content)
    title = title_match.group(1) if title_match else None

    # Extract date - handle both "By 苏剑林 | DATE" and "By Su Jianlin | DATE"
    date_match = re.search(r'By (?:苏剑林|Su Jianlin) \| ([A-Za-z]+\.? \d+, \d+)', content)
    date_str = date_match.group(1) if date_match else None

    date = None
    if date_str:
        # Try various date formats
        for fmt in ["%B %d, %Y", "%b %d, %Y", "%b. %d, %Y"]:
            try:
                date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

    return title, date, date_str

def main():
    translations_dir = Path(__file__).parent / "translations"
    articles = []
    missing = []

    for filepath in translations_dir.glob("translation_*.html"):
        title, date, date_str = extract_info(filepath)
        if title and date:
            articles.append({
                'filename': filepath.name,
                'title': title,
                'date': date,
                'date_str': date_str
            })
        else:
            missing.append(filepath.name)

    # Sort by date, most recent first
    articles.sort(key=lambda x: x['date'], reverse=True)

    # Group by year
    from collections import defaultdict
    by_year = defaultdict(list)
    for article in articles:
        by_year[article['date'].year].append(article)

    # Generate HTML
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scientific Spaces - English Translations</title>
    <style>
        body {
            margin: 48px auto;
            max-width: 68ch;
            padding: 0 16px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 18px;
            line-height: 1.65;
            color: #333;
            background: #fafafa;
        }
        h1 {
            font-size: 2.1em;
            margin-bottom: 0.5em;
            font-weight: 600;
        }
        .subtitle {
            color: #666;
            margin-bottom: 2em;
        }
        h2 {
            font-size: 1.4em;
            margin-top: 2em;
            margin-bottom: 0.5em;
            color: #444;
        }
        ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        li {
            margin: 0.6em 0;
        }
        a {
            color: #005fcc;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .date {
            color: #888;
            font-size: 0.85em;
            margin-left: 0.5em;
        }
    </style>
</head>
<body>
    <h1>Scientific Spaces</h1>
    <p class="subtitle">English translations of articles from <a href="https://kexue.fm">kexue.fm</a> by Su Jianlin (苏剑林)</p>
'''

    for year in sorted(by_year.keys(), reverse=True):
        html += f'    <h2>{year}</h2>\n    <ul>\n'
        for article in by_year[year]:
            # Show month and day only since year is in the heading
            month_day = article['date'].strftime("%b %d")
            html += f'        <li><a href="translations/{article["filename"]}">{article["title"]}</a><span class="date">{month_day}</span></li>\n'
        html += '    </ul>\n'

    html += '''</body>
</html>
'''

    output_path = Path(__file__).parent / "index.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generated index.html with {len(articles)} articles")
    if missing:
        print(f"Missing from index ({len(missing)} files - no title/date): {sorted(missing)}")

if __name__ == "__main__":
    main()
