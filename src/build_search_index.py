#!/usr/bin/env python3
"""Build a search index from all translation files."""

import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path


class TextExtractor(HTMLParser):
    """Extract text content from HTML, skipping script/style tags."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {'script', 'style', 'head'}
        self.current_skip = 0
        self.title = None
        self.in_h1 = False

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.current_skip += 1
        if tag == 'h1':
            self.in_h1 = True

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.current_skip -= 1
        if tag == 'h1':
            self.in_h1 = False

    def handle_data(self, data):
        if self.current_skip == 0:
            text = data.strip()
            if text:
                self.text_parts.append(text)
                if self.in_h1 and self.title is None:
                    self.title = text

    def get_text(self):
        return ' '.join(self.text_parts)


def extract_content(html_content):
    """Extract title and text from HTML content."""
    parser = TextExtractor()
    parser.feed(html_content)
    return parser.title, parser.get_text()


def build_index(translations_dir, exclude_files=None):
    """Build search index from all translation files."""
    index = []
    translations_path = Path(translations_dir)
    exclude_files = set(exclude_files or [])

    for html_file in sorted(translations_path.glob('translation_*.html')):
        if html_file.name in exclude_files:
            continue
        try:
            content = html_file.read_text(encoding='utf-8')
            title, text = extract_content(content)

            if title:
                # Truncate content to reasonable size for search
                # Keep first ~1200 chars of text for searching
                search_text = text[:1200] if len(text) > 1200 else text

                index.append({
                    'file': html_file.name,
                    'title': title,
                    'content': search_text
                })
        except Exception as e:
            print(f"Error processing {html_file}: {e}")

    return index


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    translations_dir = root_dir / 'translations'
    output_file = root_dir / 'search-index.js'

    # Exclude 2009 and 2014 articles
    exclude = [
        'translation_119.html', 'translation_41.html',  # 2009
        'translation_4170.html', 'translation_3171.html', 'translation_3154.html', 'translation_3150.html',  # 2014
    ]

    print(f"Building search index from {translations_dir}...")
    index = build_index(translations_dir, exclude_files=exclude)

    # Write as a JS file with a variable assignment
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('window.SEARCH_INDEX = ')
        json.dump(index, f, ensure_ascii=False)
        f.write(';\n')

    print(f"Created {output_file} with {len(index)} articles")

    # Print size info
    size_kb = output_file.stat().st_size / 1024
    print(f"Index size: {size_kb:.1f} KB")


if __name__ == '__main__':
    main()
