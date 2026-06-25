// scripts/enrich-github.mjs
//
// Enriches data/posts.json with a githubRepos field per post.
//
// What it does:
//   1. Reads data/posts.json (output of parse-snapshot.mjs).
//   2. For each post, extracts direct github.com URLs from the post text.
//   3. Resolves lnkd.in short links (HEAD with manual redirect following) to
//      their final destination. If the destination is github.com, the resolved
//      URL is added to githubRepos.
//   4. Caches resolved destinations in data/.gh-cache.json so re-runs are fast.
//   5. Writes data/posts-github.json with the githubRepos field attached.
//
// Run with:  node scripts/enrich-github.mjs
//
// Tunables:
//   CONCURRENCY   max parallel HTTP requests
//   TIMEOUT_MS    per-request timeout
//   CACHE_FILE    where to persist lnkd.in → final URL mappings

import fs from "node:fs";
import path from "node:path";
import https from "node:https";
import { fileURLToPath } from "node:url";

// Corporate networks often use TLS-inspecting proxies (Zscaler, Blue Coat)
// that present a self-signed CA. We only resolve public lnkd.in redirects,
// so disabling cert verification for this single use case is acceptable.
const httpsAgent = new https.Agent({ rejectUnauthorized: false });

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");

const INPUT = path.join(ROOT, "data", "posts.json");
const OUTPUT = path.join(ROOT, "data", "posts-github.json");
const CACHE_FILE = path.join(ROOT, "data", ".gh-cache.json");

const CONCURRENCY = 10;
const TIMEOUT_MS = 8000;

// Match github.com/{owner}/{repo}. Allows trailing path segments and query
// strings; we strip them to canonical owner/repo form for dedup.
const GH_RE =
  /^https?:\/\/(?:www\.)?github\.com\/([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)/;

const LNKD_RE = /https?:\/\/lnkd\.in\/[A-Za-z0-9_-]+/g;

function loadCache() {
  try {
    return JSON.parse(fs.readFileSync(CACHE_FILE, "utf8"));
  } catch {
    return {};
  }
}

function saveCache(cache) {
  fs.writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2), "utf8");
}

function canonicalGhUrl(url) {
  const m = url.match(GH_RE);
  if (!m) return null;
  return `https://github.com/${m[1]}/${m[2]}`;
}

// Follow redirects manually so we can record the final URL.
async function resolveUrl(url, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    let current = url;
    for (let i = 0; i < 6; i++) {
      const res = await fetch(current, {
        method: "GET",
        redirect: "manual",
        signal: controller.signal,
        headers: { "User-Agent": "curl/8.0" },
        // @ts-ignore - agent is supported on Node fetch in recent versions
        agent: httpsAgent,
      });
      if (res.status >= 300 && res.status < 400) {
        const loc = res.headers.get("location");
        if (!loc) return current;
        current = loc.startsWith("http")
          ? loc
          : new URL(loc, current).href;
        continue;
      }
      // LinkedIn sometimes returns 999 or 200 with a tracking pixel; in that
      // case current is the final URL we tried.
      return current;
    }
    return current;
  } finally {
    clearTimeout(timer);
  }
}

async function mapWithConcurrency(items, limit, fn) {
  const results = new Array(items.length);
  let idx = 0;
  async function worker() {
    while (idx < items.length) {
      const myIdx = idx++;
      try {
        results[myIdx] = await fn(items[myIdx], myIdx);
      } catch (e) {
        results[myIdx] = null;
      }
    }
  }
  await Promise.all(
    Array.from({ length: Math.min(limit, items.length) }, worker),
  );
  return results;
}

function extractDirectGithub(text) {
  const found = new Map(); // canonical url -> via
  if (!text) return found;
  const re = /https?:\/\/(?:www\.)?github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+/g;
  for (const m of text.matchAll(re)) {
    const canon = canonicalGhUrl(m[0]);
    if (canon && !found.has(canon)) found.set(canon, "text");
  }
  return found;
}

function extractLnkdLinks(posts) {
  // Build a list of {shortUrl, postIdx} so we resolve each unique URL once
  // and propagate to all posts that cite it.
  const urlToPosts = new Map();
  for (let i = 0; i < posts.length; i++) {
    for (const link of posts[i].externalLinks || []) {
      if (!/lnkd\.in/i.test(link)) continue;
      if (!urlToPosts.has(link)) urlToPosts.set(link, []);
      urlToPosts.get(link).push(i);
    }
  }
  return urlToPosts;
}

async function main() {
  if (!fs.existsSync(INPUT)) {
    console.error(`Input not found: ${INPUT}`);
    console.error("Run scripts/parse-snapshot.mjs first.");
    process.exit(1);
  }

  const data = JSON.parse(fs.readFileSync(INPUT, "utf8"));
  const posts = Array.isArray(data) ? data : data.posts || [];

  const cache = loadCache();

  // 1. Direct github URLs from text
  for (const post of posts) {
    const direct = extractDirectGithub(post.text);
    post.githubRepos = Array.from(direct, ([url, via]) => ({ url, via }));
  }

  // 2. Resolve lnkd.in short links
  const urlToPosts = extractLnkdLinks(posts);
  const uniqueUrls = [...urlToPosts.keys()];
  const uncached = uniqueUrls.filter((u) => !(u in cache));
  console.log(
    `Total posts:           ${posts.length}`,
  );
  console.log(
    `Unique lnkd.in links:  ${uniqueUrls.length} (${uncached.length} uncached)`,
  );

  if (uncached.length > 0) {
    console.log(`Resolving ${uncached.length} URLs (concurrency ${CONCURRENCY})...`);
    let done = 0;
    await mapWithConcurrency(uncached, CONCURRENCY, async (url) => {
      try {
        const final = await resolveUrl(url, TIMEOUT_MS);
        cache[url] = final;
      } catch (e) {
        cache[url] = null;
      }
      done++;
      if (done % 20 === 0 || done === uncached.length) {
        process.stdout.write(`\r  ${done}/${uncached.length}`);
      }
    });
    process.stdout.write("\n");
    saveCache(cache);
  }

  // 3. Attach resolved GitHub URLs to posts
  for (const post of posts) {
    if (!post.githubRepos) post.githubRepos = [];
    const seen = new Set(post.githubRepos.map((r) => r.url));
    for (const link of post.externalLinks || []) {
      if (!/lnkd\.in/i.test(link)) continue;
      const final = cache[link];
      if (!final) continue;
      const canon = canonicalGhUrl(final);
      if (canon && !seen.has(canon)) {
        post.githubRepos.push({ url: canon, via: "lnkd.in" });
        seen.add(canon);
      }
    }
  }

  // 4. Write output
  const out = {
    total: posts.length,
    scrapedAt: Array.isArray(data) ? null : data.scrapedAt || null,
    enrichedAt: new Date().toISOString(),
    posts,
  };
  fs.writeFileSync(OUTPUT, JSON.stringify(out, null, 2), "utf8");

  // 5. Stats
  const withGh = posts.filter((p) => (p.githubRepos || []).length > 0).length;
  const totalRepos = posts.reduce(
    (n, p) => n + (p.githubRepos || []).length,
    0,
  );
  const directOnly = posts.filter(
    (p) => (p.githubRepos || []).some((r) => r.via === "text"),
  ).length;
  const resolved = posts.filter(
    (p) => (p.githubRepos || []).some((r) => r.via === "lnkd.in"),
  ).length;

  console.log("\n=== GitHub Enrichment ===");
  console.log(`Output:                  ${OUTPUT}`);
  console.log(`Posts with GitHub repo:  ${withGh}/${posts.length}`);
  console.log(`Total GitHub links:      ${totalRepos}`);
  console.log(`  via direct text:       ${directOnly}`);
  console.log(`  via lnkd.in resolved:  ${resolved}`);
  console.log(`Cache size:              ${Object.keys(cache).length}`);
}

main().catch((e) => {
  console.error("ERROR:", e.message);
  console.error(e.stack);
  process.exit(1);
});
