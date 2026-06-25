// scripts/scrape-github-comments.mjs
//
// For each post flagged linkInComments=true, opens the post, scrolls to load
// comments, and extracts *direct* github.com/{owner}/{repo} URLs from the
// comment section. These direct URLs are stable (unlike lnkd.in which expires
// in ~24h).
//
// What it does:
//   1. Reads data/posts.json (output of parse-snapshot.mjs).
//   2. Filters posts with linkInComments=true (or with failed lnkd.in links).
//   3. Connects to Chrome Slot4 on port 5192 via DevTools Protocol.
//   4. For each candidate, navigates to the post, scrolls to bottom in steps
//      to trigger comment lazy-load, clicks "Load more comments" until gone.
//   5. Extracts direct github.com URLs from the comments container.
//   6. Writes data/posts-github.json with githubRepos attached per post.
//
// Run with:  node scripts/scrape-github-comments.mjs

import net from "node:net";
import crypto from "node:crypto";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");

const HOST = "127.0.0.1";
const PORT = 5192;
const INPUT = path.join(ROOT, "data", "posts.json");
const OUTPUT = path.join(ROOT, "data", "posts-github.json");

// ---------- HTTP / WebSocket plumbing (same pattern as scrape.mjs) ----------

function httpGet(p) {
  return new Promise((resolve, reject) => {
    http
      .get({ host: HOST, port: PORT, path: p, timeout: 5000 }, (res) => {
        let body = "";
        res.on("data", (d) => (body += d));
        res.on("end", () => resolve(body));
      })
      .on("error", reject);
  });
}

function wsConnect(urlPath) {
  return new Promise((resolve, reject) => {
    const key = crypto.randomBytes(16).toString("base64");
    const sock = net.createConnection({ host: HOST, port: PORT });
    let buffer = Buffer.alloc(0);
    let handshakeDone = false;
    let cbs = [];
    sock.on("connect", () => {
      sock.write(
        `GET ${urlPath} HTTP/1.1\r\nHost: ${HOST}:${PORT}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: ${key}\r\nSec-WebSocket-Version: 13\r\n\r\n`,
      );
    });
    sock.on("data", (chunk) => {
      buffer = Buffer.concat([buffer, chunk]);
      if (!handshakeDone) {
        const sep = buffer.indexOf("\r\n\r\n");
        if (sep < 0) return;
        const head = buffer.slice(0, sep).toString();
        buffer = buffer.slice(sep + 4);
        if (!/^HTTP\/1.1 101/.test(head)) {
          sock.destroy();
          reject(new Error("Handshake failed: " + head.split("\r\n")[0]));
          return;
        }
        handshakeDone = true;
        resolve({
          send(obj) {
            const data = Buffer.from(JSON.stringify(obj));
            const mask = crypto.randomBytes(4);
            const masked = Buffer.alloc(data.length);
            for (let i = 0; i < data.length; i++)
              masked[i] = data[i] ^ mask[i % 4];
            const len = data.length;
            let header;
            if (len < 126) header = Buffer.from([0x81, 0x80 | len]);
            else if (len < 65536) {
              header = Buffer.alloc(4);
              header[0] = 0x81;
              header[1] = 0x80 | 126;
              header.writeUInt16BE(len, 2);
            } else {
              header = Buffer.alloc(10);
              header[0] = 0x81;
              header[1] = 0x80 | 127;
              header.writeBigUInt64BE(BigInt(len), 2);
            }
            sock.write(Buffer.concat([header, mask, masked]));
          },
          onMessage(cb) {
            cbs.push(cb);
          },
          close() {
            sock.destroy();
          },
        });
      }
      while (buffer.length >= 2) {
        const b0 = buffer[0],
          b1 = buffer[1];
        const opcode = b0 & 0x0f;
        let len = b1 & 0x7f;
        let offset = 2;
        if (len === 126) {
          if (buffer.length < 4) break;
          len = buffer.readUInt16BE(2);
          offset = 4;
        } else if (len === 127) {
          if (buffer.length < 10) break;
          len = Number(buffer.readBigUInt64BE(2));
          offset = 10;
        }
        const needed = offset + len;
        if (buffer.length < needed) break;
        const payload = buffer.slice(offset, needed);
        buffer = buffer.slice(needed);
        if (opcode === 0x1) {
          try {
            const msg = JSON.parse(payload.toString());
            cbs.forEach((cb) => cb(msg));
          } catch {}
        } else if (opcode === 0x8) sock.destroy();
      }
    });
    sock.on("error", reject);
    setTimeout(() => reject(new Error("timeout")), 60000);
  });
}

// ---------- GitHub URL helpers ----------

const GH_RE =
  /^https?:\/\/(?:www\.)?github\.com\/([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)/;

function canonicalGhUrl(url) {
  const m = String(url).match(GH_RE);
  if (!m) return null;
  return `https://github.com/${m[1]}/${m[2]}`;
}

// Strip common non-repo paths (issues, pulls, blob, tree, etc.) — they all
// belong to the same repo. We keep only owner/repo for dedup / display.
function isRepoUrl(url) {
  return canonicalGhUrl(url) !== null;
}

// ---------- Main ----------

(async () => {
  if (!fs.existsSync(INPUT)) {
    console.error(`Input not found: ${INPUT}`);
    console.error("Run scripts/parse-snapshot.mjs first.");
    process.exit(1);
  }

  const posts = JSON.parse(fs.readFileSync(INPUT, "utf8"));
  const allCandidates = posts.filter((p) => p.linkInComments && p.postUrl);
  const limit = process.argv[2] ? parseInt(process.argv[2], 10) : null;
  const candidates = limit ? allCandidates.slice(0, limit) : allCandidates;
  console.log(`Total posts:         ${posts.length}`);
  console.log(`linkInComments:      ${allCandidates.length}`);
  if (limit) console.log(`Limiting to first ${limit} for this run`);

  // Connect to Chrome
  console.log("\nConnecting to Chrome DevTools on port " + PORT + "...");
  const versionRaw = await httpGet("/json/version");
  const version = JSON.parse(versionRaw);
  const wsPath = version.webSocketDebuggerUrl.replace(
    `ws://${HOST}:${PORT}`,
    "",
  );
  const ws = await wsConnect(wsPath);
  console.log("Connected.");

  let id = 1;
  const pending = new Map();
  ws.onMessage((msg) => {
    if (msg.id && pending.has(msg.id)) {
      const p = pending.get(msg.id);
      pending.delete(msg.id);
      p.resolve(msg);
    }
  });
  const send = (method, params = {}, sessionId) =>
    new Promise((resolve) => {
      const reqId = id++;
      pending.set(reqId, { resolve });
      const msg = { id: reqId, method, params };
      if (sessionId) msg.sessionId = sessionId;
      ws.send(msg);
    });

  // Open a fresh tab to keep this scrape isolated from any other Chrome state.
  const {
    result: { targetId },
  } = await send("Target.createTarget", { url: "about:blank" });
  const {
    result: { sessionId },
  } = await send("Target.attachToTarget", {
    targetId,
    flatten: true,
  });
  console.log(`Opened isolated tab: ${targetId}`);

  await send("Page.enable", {}, sessionId);
  await send("Runtime.enable", {}, sessionId);

  // Navigate to about:blank first so each Page.navigate is a full load.
  await send("Page.navigate", { url: "about:blank" }, sessionId);
  await new Promise((r) => setTimeout(r, 800));

  // Per-post extraction. We keep this sequential in a single tab — opening
  // many tabs in parallel against one Chrome instance fights for resources.
  const results = new Map(); // activityId -> [{url, via}]
  let found = 0;

  for (let i = 0; i < candidates.length; i++) {
    const post = candidates[i];
    process.stdout.write(
      `\r[${i + 1}/${candidates.length}] ${post.authorName.padEnd(22)} (${(post.timestamp || "").padEnd(4)}) `,
    );

    try {
      await send("Page.navigate", { url: post.postUrl }, sessionId);
      // Wait for initial paint + post body to render
      await new Promise((r) => setTimeout(r, 3500));

      // Scroll in steps to trigger lazy-load of comments
      for (let s = 0; s < 6; s++) {
        await send(
          "Runtime.evaluate",
          {
            expression:
              "window.scrollTo({top: document.body.scrollHeight, behavior: 'instant'});",
            returnByValue: true,
          },
          sessionId,
        );
        await new Promise((r) => setTimeout(r, 1500));
      }

      // Click any "Load previous comments" / "View more comments" buttons
      for (let attempts = 0; attempts < 4; attempts++) {
        const clickResp = await send(
          "Runtime.evaluate",
          {
            expression: `(function() {
              const btns = Array.from(document.querySelectorAll('button, [role="button"]'));
              const re = /load.*previous.*comment|view.*previous.*comment|show.*previous.*comment|load.*more.*comment|view.*more.*comment/i;
              const targets = btns.filter(b => re.test(b.textContent || ''));
              if (targets.length) {
                targets[0].click();
                return 'clicked:' + targets.length;
              }
              return 'none';
            })()`,
            returnByValue: true,
          },
          sessionId,
        );
        const v = clickResp.result?.result?.value || "none";
        if (v === "none") break;
        await new Promise((r) => setTimeout(r, 2000));
      }

      // Extract direct github.com URLs from anywhere in the post+comments DOM
      const extractResp = await send(
        "Runtime.evaluate",
        {
          expression: `(function() {
            const seen = new Map(); // canonical url -> first href source
            const re = /https?:\\/\\/(?:www\\.)?github\\.com\\/[A-Za-z0-9_.-]+\\/[A-Za-z0-9_.-]+/g;
            // Scan anchors everywhere on the post-detail page
            document.querySelectorAll('a[href]').forEach(a => {
              const href = a.getAttribute('href') || '';
              const matches = href.match(re);
              if (!matches) return;
              for (const m of matches) {
                const mm = m.match(/github\\.com\\/([\\w.-]+)\\/([\\w.-]+)/);
                if (!mm) continue;
                const canon = 'https://github.com/' + mm[1] + '/' + mm[2];
                if (!seen.has(canon)) seen.set(canon, 'comments');
              }
            });
            // Also scan text nodes (some people paste a URL inline)
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
            let node;
            while ((node = walker.nextNode())) {
              const matches = (node.textContent || '').match(re);
              if (!matches) continue;
              for (const m of matches) {
                const mm = m.match(/github\\.com\\/([\\w.-]+)\\/([\\w.-]+)/);
                if (!mm) continue;
                const canon = 'https://github.com/' + mm[1] + '/' + mm[2];
                if (!seen.has(canon)) seen.set(canon, 'text');
              }
            }
            return JSON.stringify([...seen.entries()]);
          })()`,
          returnByValue: true,
        },
        sessionId,
      );

      const raw = extractResp.result?.result?.value || "[]";
      const pairs = JSON.parse(raw);
      if (pairs.length > 0) {
        results.set(post.activityId, pairs.map(([url, via]) => ({ url, via })));
        found++;
        process.stdout.write(`→ ${pairs.length} repo(s)\n`);
      } else {
        results.set(post.activityId, []);
        process.stdout.write(`→ 0\n`);
      }
    } catch (e) {
      console.error(`\n  Error on ${post.activityId}: ${e.message}`);
      results.set(post.activityId, []);
    }
  }

  // Merge into all posts (preserving the existing githubRepos from enrich-github.mjs
  // if present, layering comments-extracted repos on top).
  for (const post of posts) {
    const existing = Array.isArray(post.githubRepos) ? post.githubRepos : [];
    const seen = new Set(existing.map((r) => r.url));
    const comments = results.get(post.activityId) || [];
    const merged = [...existing];
    for (const r of comments) {
      if (!seen.has(r.url)) {
        merged.push(r);
        seen.add(r.url);
      }
    }
    post.githubRepos = merged;
  }

  // Close the tab we opened
  try {
    await send("Target.closeTarget", { targetId }, sessionId);
  } catch {}
  ws.close();

  const out = {
    total: posts.length,
    candidates: candidates.length,
    enrichedAt: new Date().toISOString(),
    postsWithGithubRepos: posts.filter((p) => p.githubRepos.length > 0).length,
    posts,
  };
  fs.writeFileSync(OUTPUT, JSON.stringify(out, null, 2), "utf8");

  console.log("\n=== Comment scrape complete ===");
  console.log(`Output:                ${OUTPUT}`);
  console.log(`Candidates visited:    ${candidates.length}`);
  console.log(`Posts w/ GitHub repos: ${out.postsWithGithubRepos}`);
  console.log(`Total GitHub links:    ${posts.reduce((n, p) => n + p.githubRepos.length, 0)}`);

  // Sample
  const withGh = posts.filter((p) => p.githubRepos.length > 0);
  console.log("\nSample of found repos:");
  withGh.slice(0, 8).forEach((p) => {
    const repos = p.githubRepos.map((r) => r.url.replace("https://github.com/", ""));
    console.log(`  ${p.authorName} (${p.timestamp}): ${repos.join(", ")}`);
  });
})().catch((e) => {
  console.error("ERROR:", e.message);
  console.error(e.stack);
  process.exit(1);
});
