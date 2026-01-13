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
    root_dir = Path(__file__).parent.parent
    translations_dir = root_dir / "translations"
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

    # Get sorted years for navigation
    years = sorted(by_year.keys(), reverse=True)

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
            max-width: 72ch;
            padding: 0 20px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 17px;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
        }
        h1 {
            font-size: 2.2em;
            margin-bottom: 0.3em;
            font-weight: 700;
            color: #1a1a2e;
        }
        .subtitle {
            color: #555;
            margin-bottom: 2.5em;
            font-size: 1.05em;
        }
        .subtitle a {
            color: #2563eb;
        }
        h2 {
            font-size: 1.1em;
            font-weight: 600;
            margin-top: 2.5em;
            margin-bottom: 1em;
            color: #fff;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 0.6em 1em;
            border-radius: 6px;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        li {
            margin: 0;
            padding: 0.75em 1em;
            border-radius: 6px;
            transition: background-color 0.15s ease;
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 1em;
        }
        li:hover {
            background-color: #e8f0fe;
        }
        li:nth-child(odd) {
            background-color: #fff;
        }
        li:nth-child(even) {
            background-color: #f8f9fa;
        }
        li:nth-child(odd):hover,
        li:nth-child(even):hover {
            background-color: #e8f0fe;
        }
        a {
            color: #1a56db;
            text-decoration: none;
            flex: 1;
        }
        a:hover {
            color: #1e40af;
            text-decoration: underline;
        }
        .date {
            color: #6b7280;
            font-size: 0.85em;
            white-space: nowrap;
            font-variant-numeric: tabular-nums;
        }

        /* Year navigation */
        .year-nav {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 0.5em;
            margin-bottom: 2em;
            padding: 1em;
            background: #fff;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
        }
        .year-nav a {
            padding: 0.4em 0;
            width: 4.5em;
            text-align: center;
            background: #f3f4f6;
            border-radius: 4px;
            font-size: 0.9em;
            font-weight: 500;
            color: #374151;
        }
        .year-nav a:hover {
            background: #1a1a2e;
            color: #fff;
            text-decoration: none;
        }

        /* Month grouping */
        .month-group {
            margin-top: 1.2em;
            margin-bottom: 0.5em;
            padding-left: 1em;
            font-size: 0.8em;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .month-group:first-of-type {
            margin-top: 0;
        }

        /* Search */
        .search-container {
            margin-bottom: 1.5em;
        }
        .search-box {
            width: 100%;
            padding: 0.75em 1em;
            font-size: 1em;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            background: #fff;
            color: #333;
            outline: none;
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }
        .search-box:focus {
            border-color: #1a56db;
            box-shadow: 0 0 0 3px rgba(26, 86, 219, 0.1);
        }
        .search-box::placeholder {
            color: #9ca3af;
        }
        .search-results {
            font-size: 0.85em;
            color: #6b7280;
            margin-top: 0.5em;
            padding-left: 0.25em;
        }
        .hidden {
            display: none !important;
        }
        .no-results {
            text-align: center;
            padding: 3em 1em;
            color: #6b7280;
        }
    </style>
</head>
<body>
    <h1>Scientific Spaces</h1>
    <p class="subtitle">English translations of articles from <a href="https://kexue.fm">kexue.fm</a> by Su Jianlin (苏剑林)</p>

    <div class="search-container">
        <input type="text" class="search-box" id="search" placeholder="Search articles..." autocomplete="off">
        <div class="search-results" id="search-results"></div>
    </div>

    <nav class="year-nav" id="year-nav"></nav>

'''

    for year in years:
        html += f'    <h2 id="y{year}">{year}</h2>\n    <ul>\n'
        for article in by_year[year]:
            # Show month and day only since year is in the heading
            month_day = article['date'].strftime("%b %d")
            html += f'        <li><a href="translations/{article["filename"]}">{article["title"]}</a><span class="date">{month_day}</span></li>\n'
        html += '    </ul>\n'

    html += '''
    <script src="search-index.js"></script>
    <script>
    (function() {
        const searchIndex = window.SEARCH_INDEX || [];
        const searchInput = document.getElementById('search');
        const searchResults = document.getElementById('search-results');
        const yearNav = document.getElementById('year-nav');
        const yearSections = document.querySelectorAll('h2[id^="y"]');
        const allLists = document.querySelectorAll('body > ul');

        // Generate year nav buttons from year headers
        yearSections.forEach(h2 => {
            const a = document.createElement('a');
            a.href = '#' + h2.id;
            a.textContent = h2.textContent;
            yearNav.appendChild(a);
        });

        // Build a map from filename to list item
        const fileToItem = new Map();
        document.querySelectorAll('li > a[href^="translations/"]').forEach(a => {
            const filename = a.getAttribute('href').replace('translations/', '');
            fileToItem.set(filename, a.parentElement);
        });

        function search(query) {
            if (!query.trim()) {
                resetView();
                return;
            }

            const terms = query.toLowerCase().split(/\\s+/).filter(t => t.length > 0);
            const results = [];

            for (const item of searchIndex) {
                const titleLower = item.title.toLowerCase();
                const contentLower = item.content.toLowerCase();
                const combined = titleLower + ' ' + contentLower;

                // Check if all terms match
                const allMatch = terms.every(term => combined.includes(term));
                if (allMatch) {
                    // Score: title matches are weighted higher
                    let score = 0;
                    for (const term of terms) {
                        if (titleLower.includes(term)) score += 10;
                        if (contentLower.includes(term)) score += 1;
                    }
                    results.push({ ...item, score });
                }
            }

            // Sort by score descending
            results.sort((a, b) => b.score - a.score);

            displayResults(results, query);
        }

        function displayResults(results, query) {
            // Hide year nav and all sections
            yearNav.classList.add('hidden');
            yearSections.forEach(h => h.classList.add('hidden'));
            allLists.forEach(ul => ul.classList.add('hidden'));

            // Hide all list items first
            fileToItem.forEach(li => li.classList.add('hidden'));

            if (results.length === 0) {
                searchResults.textContent = `No results for "${query}"`;
                return;
            }

            searchResults.textContent = `${results.length} result${results.length === 1 ? '' : 's'}`;

            // Show matching items and their parent lists
            const visibleLists = new Set();
            for (const result of results) {
                const li = fileToItem.get(result.file);
                if (li) {
                    li.classList.remove('hidden');
                    const parentUl = li.parentElement;
                    if (parentUl) {
                        parentUl.classList.remove('hidden');
                        visibleLists.add(parentUl);
                    }
                }
            }

            // Show year headers for visible lists
            visibleLists.forEach(ul => {
                const prevH2 = ul.previousElementSibling;
                if (prevH2 && prevH2.tagName === 'H2') {
                    prevH2.classList.remove('hidden');
                }
            });
        }

        function resetView() {
            searchResults.textContent = '';
            yearNav.classList.remove('hidden');
            yearSections.forEach(h => h.classList.remove('hidden'));
            allLists.forEach(ul => ul.classList.remove('hidden'));
            fileToItem.forEach(li => li.classList.remove('hidden'));
        }

        // Debounce search
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => search(e.target.value), 150);
        });

        // Clear on Escape
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchInput.value = '';
                resetView();
            }
        });
    })();
    </script>
</body>
</html>
'''

    output_path = root_dir / "index.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generated index.html with {len(articles)} articles")
    if missing:
        print(f"Missing from index ({len(missing)} files - no title/date): {sorted(missing)}")

if __name__ == "__main__":
    main()
