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

## Requirements

Set these environment variables:
- `EXA_API_KEY` - for fetching content
- `FIRECRAWL_API_KEY` - fallback fetcher
- `OPENROUTER_API_KEY` - for translation (Gemini 3 Flash)
