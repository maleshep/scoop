# Scoop 🐼

Extract your LinkedIn saved posts into a structured research index.

## What it does

- Connects to Chrome via DevTools Protocol (CDP)
- Clicks "Show more results" to load all saved posts
- Extracts author names, timestamps, post text, external links
- Detects "link in comments" patterns for GitHub repos
- Outputs structured JSON and generates a Markdown index

## Setup

### 1. Create a dedicated Chrome profile

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=5192 `
  --remote-debugging-address=127.0.0.1 `
  --user-data-dir="$env:LOCALAPPDATA\Google\Chrome\Slot4" `
  --profile-directory=Default `
  --no-first-run `
  --no-default-browser-check `
  "https://www.linkedin.com/login"
```

Sign into LinkedIn in the Chrome window that opens. The session persists in Slot4.

### 2. Add the MCP server

Add to your `.mcp.json` or Zed's `settings.json`:

```json
"chrome-research": {
  "command": "npx",
  "args": [
    "-y", "chrome-devtools-mcp@latest",
    "--browserUrl", "http://127.0.0.1:5192",
    "--no-usage-statistics",
    "--experimental-page-id-routing"
  ]
}
```

### 3. Sync your saved posts

Launch Chrome with the research profile, then tell your AI agent:
> "Sync my saved articles"

The agent will use the `chrome_research_*` MCP tools to scrape all posts and generate your research index.

## Architecture

```
Chrome (Slot4) → DevTools port 5192 → MCP server → AI agent → Research index
```

## Files

- `scripts/launch.ps1` — Launch Chrome with the research profile
- `scripts/scrape.mjs` — CDP-based LinkedIn saved posts scraper
- `lib/cdp-client.mjs` — Reusable WebSocket/CDP client
- `lib/extractor.mjs` — Post extraction logic

## License

MIT
