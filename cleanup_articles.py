#!/usr/bin/env python3
"""Clean up quirks in translated articles."""

import re
from pathlib import Path


def cleanup_article(content: str) -> str:
    """Clean up various non-standard elements from an article."""

    # 1. Remove hashtag anchor links from headings
    # Pattern: <a href="...#...">#</a> or <a id="..." href="#...">#</a>
    content = re.sub(r'\s*<a\s+(?:id="[^"]*"\s+)?href="[^"]*#[^"]*">#</a>', '', content)

    # 2. Remove Chinese IDs from heading tags but keep the heading
    # Pattern: <h2 id="本文小结"> -> <h2>
    content = re.sub(r'(<h[1-6])\s+id="[^"]*">', r'\1>', content)

    # 3. Remove "Original Address" sections (various formats)
    # These appear before the footer and are redundant
    patterns = [
        # <hr />\n<p><em><strong>Original Address:</strong>...</em></p>\n<hr>
        r'<hr\s*/?\s*>\s*\n\s*<p><em><strong>Original Address:</strong>.*?</em></p>\s*\n\s*<hr\s*/?\s*>',
        # <p><em><strong>Original Address:</strong>...</em></p>
        r'<p><em><strong>Original Address:</strong>.*?</em></p>\s*',
        # <p>Original Address: ...</p>
        r'<p>\s*Original Address:\s*<a[^>]*>.*?</a>\s*</p>\s*',
        # <em>Original Address: ...</em> (standalone)
        r'^\s*<em>Original Address:\s*<a[^>]*>.*?</a></em>\s*$',
        # Original Address: ... (standalone line)
        r'^\s*Original Address:\s*<a[^>]*>.*?</a>\s*$',
    ]
    for pattern in patterns:
        content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)

    # 4. Clean up any double <hr> tags that might result
    content = re.sub(r'(<hr\s*/?\s*>)\s*\n\s*(<hr\s*/?\s*>)', r'\1', content)

    # 5. Remove excessive blank lines (more than 2 consecutive)
    content = re.sub(r'\n{4,}', '\n\n\n', content)

    return content


def main():
    translations_dir = Path(__file__).parent / 'translations'

    fixed_count = 0
    for html_file in sorted(translations_dir.glob('translation_*.html')):
        content = html_file.read_text(encoding='utf-8')
        new_content = cleanup_article(content)

        if new_content != content:
            html_file.write_text(new_content, encoding='utf-8')
            fixed_count += 1
            print(f"Fixed: {html_file.name}")

    print(f"\nTotal files fixed: {fixed_count}")


if __name__ == '__main__':
    main()
