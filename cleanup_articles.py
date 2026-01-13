#!/usr/bin/env python3
"""Clean up quirks in translated articles."""

import re
from pathlib import Path


def cleanup_article(content: str) -> str:
    """Clean up various non-standard elements from an article."""

    # ========== HEADING CLEANUP ==========

    # 1. Remove hashtag anchor links from headings (multiple formats)
    # Format: <a href="...#...">#</a>
    content = re.sub(r'\s*<a\s+href="[^"]*#[^"]*">#</a>', '', content)
    # Format: <a id="..." href="#...">#</a>
    content = re.sub(r'\s*<a\s+id="[^"]*"\s+href="#[^"]*">#</a>', '', content)
    # Format: <a name="..." href="#...">#</a>
    content = re.sub(r'\s*<a\s+name="[^"]*"\s+href="#[^"]*">#</a>', '', content)
    # Format: <a href="https://kexue.fm/archives/XXXX#...">#</a>
    content = re.sub(r'\s*<a\s+href="https?://kexue\.fm/archives/\d+#[^"]*">#</a>', '', content)

    # 2. Remove Chinese IDs from heading tags but keep the heading
    # Pattern: <h2 id="本文小结"> -> <h2>
    content = re.sub(r'(<h[1-6])\s+id="[^"]*">', r'\1>', content)

    # ========== REPRINT/REPOST NOTICES ==========

    # 3. Remove "Reprinted/Reposted with/from address" lines (various formats)
    reprint_patterns = [
        # <p><em><strong>Reprinted with the address:</strong> <a>...</a></em></p>
        r'<p>\s*<em>\s*<strong>\s*Reprinted?\s+(?:with|from|at)?\s*(?:the\s+)?(?:original\s+)?address[:\s]*</strong>\s*<a[^>]*>[^<]*</a>\s*</em>\s*</p>\s*',
        # <p><i><strong>Reprinted from:</strong>...</i></p>
        r'<p>\s*<i>\s*<strong>\s*Reprinted?\s+(?:from|at)[:\s]*</strong>\s*<a[^>]*>[^<]*</a>\s*</i>\s*</p>\s*',
        # <p><em><strong>Reprinted from:</strong>...</em></p>
        r'<p>\s*<em>\s*<strong>\s*Reprinted?\s+(?:from|at)[:\s]*</strong>\s*<a[^>]*>[^<]*</a>\s*</em>\s*</p>\s*',
        # <p><i><b>Reprint Address: </b>...</i></p>
        r'<p>\s*<i>\s*<b>\s*Reprint(?:ed)?\s+Address[:\s]*</b>\s*<a[^>]*>[^<]*</a>\s*</i>\s*</p>\s*',
        # <em><strong>Reprinting: Please include...</strong>...</em>
        r'<em>\s*<strong>\s*Reprinting[:\s]+Please[^<]*</strong>\s*<a[^>]*>[^<]*</a>\s*</em>\s*(?:<br\s*/?>)?\s*',
        # <em><strong>When reprinting/reposting, please include...</strong>...</em>
        r'<em>\s*<strong>\s*When\s+re(?:print|post)ing,?\s+please\s+include[^<]*</strong>\s*<a[^>]*>[^<]*</a>\s*</em>\s*(?:<br\s*/?>)?\s*',
        # <em><strong>Reprinted with the original address:</strong>...</em> (not in <p>)
        r'<em>\s*<strong>\s*Reprinted?\s+(?:with|from|at)?\s*(?:the\s+)?(?:original\s+)?address[:\s]*</strong>\s*<a[^>]*>[^<]*</a>\s*</em>\s*',
        # <em><strong>Reprinted please include...</strong>...</em>
        r'<em>\s*<strong>\s*Reprinted?\s+(?:please\s+)?include[^<]*</strong>\s*<a[^>]*>[^<]*</a>\s*</em>\s*(?:<br\s*/?>)?\s*',
        # <em><strong>Reprinted from:</strong> [markdown link]</em>
        r'<em>\s*<strong>\s*Reprinted?\s+(?:from|at)[:\s]*</strong>\s*\[[^\]]*\]\([^)]*\)\s*</em>\s*(?:<br\s*/?>)?\s*',
        # <strong>Please include the original address when reposting:</strong>...
        r'<strong>\s*Please\s+include[^<]*(?:when\s+)?re(?:print|post)ing[:\s]*</strong>\s*<a[^>]*>[^<]*</a>\s*(?:<br\s*/?>)?\s*',
        # Reprinted to please include this article address:...
        r'Reprinted?\s+to\s+please\s+include[^<]*<a[^>]*>[^<]*</a>\s*(?:<br\s*/?>)?\s*',
        # <p>Reprinted from: ...</p>
        r'<p>\s*Reprinted?\s+(?:from|at)[:\s]*<a[^>]*>[^<]*</a>\s*</p>\s*',
    ]
    for pattern in reprint_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)

    # ========== FAQ REFERENCES ==========

    # 4. Remove "For more detailed reprinting/reposting/reproduction matters, please refer to: FAQ" lines
    # These are boilerplate links to the site's FAQ about reprinting policy
    faq_patterns = [
        # Any paragraph containing "FAQ" and linking to kexue.fm FAQ
        r'<p>\s*(?:<[ieb]>|<em>|<strong>)*\s*(?:For\s+(?:more\s+)?detail[^<]*|Reference\s+for\s+reprint[^<]*|Reprinting\s+rules[^<]*)[^<]*(?:</[ieb]>|</em>|</strong>)*\s*(?:<[ieb]>|<em>|<strong>)*[^<]*(?:</[ieb]>|</em>|</strong>)*\s*<a[^>]*(?:6508|faq)[^>]*>[^<]*</a>\s*(?:</[ieb]>|</em>|</strong>)*\s*</p>\s*',
        # Without <p> wrapper
        r'(?:<[ieb]>|<em>|<strong>)+\s*For\s+(?:more\s+)?detail[^<]*(?:</[ieb]>|</em>|</strong>)*\s*<a[^>]*(?:6508|faq)[^>]*>[^<]*</a>\s*(?:</[ieb]>|</em>|</strong>)*\s*(?:<br\s*/?>)?\s*',
        # Simpler: any line with "refer to" and FAQ link
        r'(?:please\s+)?refer\s+to[:\s]*<a[^>]*(?:6508|faq\.html)[^>]*>[^<]*FAQ[^<]*</a>\s*(?:</[ieb]>|</em>|</strong>)*\.?\s*(?:</p>)?\s*',
        # Standalone: For more details/information on reposting...
        r'For\s+more\s+(?:detailed?\s+)?(?:information\s+on\s+)?(?:reproduction|reprinting|reposting|reprint)\s+(?:matters)?[^<]*<a[^>]*>[^<]*</a>\s*(?:<br\s*/?>)?\s*',
        # <i><b>Reference for reprint:</b>...</i>
        r'<i>\s*<b>\s*Reference\s+for\s+reprint[:\s]*</b>\s*<a[^>]*>[^<]*</a>\s*</i>\s*',
        # For detailed reprinting matters, please refer to: <a>FAQ</a>
        r'For\s+(?:more\s+)?detail(?:ed)?\s+(?:reprinting|reposting|reproduction)\s+(?:matters|guidelines)?[,\s]*(?:please\s+)?refer\s+to[:\s]*<a[^>]*>[^<]*FAQ[^<]*</a>\s*',
        # <em><strong>Detailed Reprinting Guidelines:</strong>...</em>
        r'<em>\s*<strong>\s*Detail(?:ed)?\s+(?:Reprinting|Reposting)\s+Guidelines?[:\s]*</strong>\s*<a[^>]*>[^<]*</a>\s*</em>\s*',
        # Multi-line: Reprint address:...<br>For more details...
        r'<p>\s*Reprint\s+address[:\s]*<a[^>]*>[^<]*</a>\s*<br\s*/?>\s*For\s+more\s+details[^<]*<a[^>]*>[^<]*</a>\s*</p>\s*',
    ]
    for pattern in faq_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)

    # ========== CITATION REQUESTS ==========

    # 5. Remove "If you need to cite this article" sections
    cite_patterns = [
        # <p><strong>If you need to cite this article, please refer to:</strong></p>
        r'<p>\s*<strong>\s*If\s+you\s+need\s+to\s+cite\s+this\s+article[^<]*</strong>\s*</p>\s*',
        # <strong>If you need to cite this article...</strong>
        r'<strong>\s*If\s+you\s+need\s+to\s+cite\s+this\s+article[^<]*</strong>\s*(?:<br\s*/?>)?\s*',
        # If you need to cite this article, please refer to:
        r'If\s+you\s+need\s+to\s+cite\s+this\s+article[^<]*(?:<br\s*/?>)?\s*',
        # <p>If you need to cite this article...</p>
        r'<p>\s*If\s+you\s+need\s+to\s+cite\s+this\s+article[^<]*</p>\s*',
    ]
    for pattern in cite_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)

    # 6. Remove citation paragraphs (Su Jianlin. (date). "title"...)
    content = re.sub(
        r'<p>\s*Su\s+Jianlin\.\s*\([^)]+\)\.\s*"[^"]+"\s*(?:\[Blog\s+post\])?\.\s*(?:Retrieved\s+from\s*)?(?:<a[^>]*>[^<]*</a>|https?://[^\s<]+)\s*</p>\s*',
        '',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )

    # ========== BIBTEX BLOCKS ==========

    # 7. Remove BibTeX code blocks
    content = re.sub(
        r'<pre><code>\s*@(?:online|article|misc)\s*\{[^}]*\}[^<]*</code></pre>\s*',
        '',
        content,
        flags=re.DOTALL
    )
    # Also plain BibTeX without pre/code
    content = re.sub(
        r'@(?:online|article|misc)\s*\{\s*kexuefm-\d+\s*,[^}]+\}\s*',
        '',
        content,
        flags=re.DOTALL
    )

    # ========== ORIGINAL ADDRESS ==========

    # 8. Remove "Original Address" sections (various formats)
    original_patterns = [
        # <hr />\n<p><em><strong>Original Address:</strong>...</em></p>\n<hr>
        r'<hr\s*/?\s*>\s*\n?\s*<p><em><strong>Original Address:</strong>.*?</em></p>\s*\n?\s*<hr\s*/?\s*>',
        # <p><em><strong>Original Address:</strong>...</em></p>
        r'<p>\s*<em>\s*<strong>\s*Original\s+Address[:\s]*</strong>.*?</em>\s*</p>\s*',
        # <p>Original Address: ...</p>
        r'<p>\s*Original\s+Address[:\s]*<a[^>]*>.*?</a>\s*</p>\s*',
        # <em>Original Address: ...</em> (standalone)
        r'^\s*<em>\s*Original\s+Address[:\s]*<a[^>]*>.*?</a>\s*</em>\s*$',
        # Original Address: ... (standalone line)
        r'^\s*Original\s+Address[:\s]*<a[^>]*>.*?</a>\s*$',
    ]
    for pattern in original_patterns:
        content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)

    # ========== COMMENT SECTION REFERENCES ==========

    # 9. Remove "If you have any doubts/suggestions, please continue the discussion in the comments section" lines
    comment_patterns = [
        r'<p>\s*<strong>\s*If\s+you\s+have\s+any\s+(?:doubts?|questions?|suggestions?)[^<]*(?:comments?\s+section|discussion)[^<]*</strong>\s*</p>\s*',
        r'<p>\s*If\s+you\s+have\s+any\s+(?:doubts?|questions?|suggestions?)[^<]*(?:comments?\s+section|discussion)[^<]*</p>\s*',
        r'<strong>\s*If\s+you\s+have\s+any\s+(?:doubts?|questions?|suggestions?)[^<]*(?:comments?\s+section|discussion)[^<]*</strong>\s*',
    ]
    for pattern in comment_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)

    # ========== REFERENCE FOR CITATION ==========

    # 10. Remove "Reference for citation:" blocks
    content = re.sub(
        r'<p>\s*<strong>\s*Reference\s+for\s+citation[:\s]*</strong>\s*</p>\s*',
        '',
        content,
        flags=re.IGNORECASE
    )

    # ========== CLEANUP ==========

    # 11. Clean up any double <hr> tags that might result
    content = re.sub(r'(<hr\s*/?\s*>)\s*\n?\s*(<hr\s*/?\s*>)', r'\1', content)

    # 12. Remove orphaned <hr> before footer
    content = re.sub(r'<hr\s*/?\s*>\s*\n?\s*(<hr>\s*\n?\s*<footer)', r'\1', content)

    # 13. Remove empty paragraphs
    content = re.sub(r'<p>\s*</p>\s*', '', content)

    # 14. Remove excessive blank lines (more than 2 consecutive)
    content = re.sub(r'\n{4,}', '\n\n\n', content)

    # 15. Clean up whitespace before footer
    content = re.sub(r'\n{3,}(<hr>\s*\n\s*<footer)', r'\n\n\1', content)

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
