# kexue-en
English translation of kexue.fm

## Adding a New Post

```bash
python translate.py add https://kexue.fm/archives/12345
# or just the ID:
python translate.py add 12345
```

This will fetch, translate, and update the index automatically.

Use `--force` to re-translate an existing article.

## Adding Comments to a Post

```bash
python src/translate.py addcomments https://kexue.fm/archives/12345
# or just the ID:
python src/translate.py addcomments 12345
```

This will use cached data to translate and append a comments section to an existing translation. The article must already be translated and cached locally using the `python translate.py add`.

Use `--force` to re-translate an existing comment section (original text loaded from cache). In order update the cache, you must run the previous command with `--force`.

## Requirements

Set these environment variables:
- `EXA_API_KEY` - for fetching content
- `FIRECRAWL_API_KEY` - fallback fetcher
- `OPENROUTER_API_KEY` - for translation (Gemini 3 Flash)
