# Chrome Research Profile Setup

Dedicated Chrome instance for scraping LinkedIn saved posts. Separate from chrome-dog (Slot3/port 9223) and chrome-cat (Slot2/port 9224).

## Architecture

```
chrome-dog      →  Slot3  →  port 9223  →  chrome_dog_* tools       (reserved)
chrome-cat      →  Slot2  →  port 9224  →  chrome_cat_* tools       (reserved)
chrome-research →  Slot4  →  port 5192  →  chrome_research_* tools  (this repo)
```

## One-time setup (DONE)

- [x] Created `Slot4` user-data-dir at `C:\Users\M316235\AppData\Local\Google\Chrome\Slot4`
- [x] Added `chrome-research` MCP server to `.mcp.json` (project-level)
- [x] Added `chrome-research` MCP server to Zed's `settings.json` (user-level)
- [x] Signed into LinkedIn in Slot4 (li_at cookie present, 53KB cookies file)
- [x] Scraper verified working (443 posts scraped on 6/21/26)

## How to sync

### Step 1: Launch Chrome with Slot4

```powershell
# From the research repo:
.\scripts\launch-research.ps1

# Or manually:
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=5192 `
  --remote-debugging-address=127.0.0.1 `
  --user-data-dir="C:\Users\M316235\AppData\Local\Google\Chrome\Slot4" `
  --profile-directory=Default `
  --no-first-run `
  --no-default-browser-check `
  "https://www.linkedin.com/my-items/saved-posts/?savedPostType=ALL"
```

### Step 2: Wait for LinkedIn to load

The LinkedIn session should persist from the previous login. If it redirects to login, sign in again.

### Step 3: Tell the agent

Say: **"sync my saved articles"**

The agent will:
1. Connect to Chrome on port 5192 via DevTools Protocol
2. Click "Show more results" to load all saved posts
3. Extract every post with timestamps, author names, text, and external links
4. Save to `data/linkedin-saved.json`
5. Update `README.md` with proper dates and links

## Restart Zed

After the one-time setup, restart Zed to pick up the `chrome-research` MCP server. You'll then have `chrome_research_*` tools available alongside `chrome_cat_*` and `chrome_dog_*`.
