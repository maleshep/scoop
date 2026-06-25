// Scrape LinkedIn saved posts using anchor-based extraction
// LinkedIn's saved-posts page uses a different DOM structure than the main feed.
// Posts are found via a[href*="/feed/update/urn:li:activity:"] anchors.

import net from "node:net";
import crypto from "node:crypto";
import fs from "node:fs";
import http from "node:http";

const HOST = "127.0.0.1";
const PORT = 5192;

function httpGet(path) {
  return new Promise((resolve, reject) => {
    http
      .get({ host: HOST, port: PORT, path, timeout: 5000 }, (res) => {
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
        if (!/^HTTP\/1\.1 101/.test(head)) {
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

(async () => {
  try {
    const versionRaw = await httpGet("/json/version");
    const version = JSON.parse(versionRaw);
    const wsPath = version.webSocketDebuggerUrl.replace(
      `ws://${HOST}:${PORT}`,
      "",
    );
    console.log("Connecting to Chrome DevTools...");
    const ws = await wsConnect(wsPath);
    console.log("Connected!");

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

    const {
      result: { targetInfos },
    } = await send("Target.getTargets");
    const linkedin = targetInfos.find(
      (t) => t.type === "page" && t.url.includes("linkedin.com"),
    );
    if (!linkedin) {
      console.error("No LinkedIn tab!");
      process.exit(1);
    }
    console.log("Found LinkedIn tab:", linkedin.title);

    const {
      result: { sessionId },
    } = await send("Target.attachToTarget", {
      targetId: linkedin.targetId,
      flatten: true,
    });
    console.log("Attached to tab");

    // Step 1: Click "Show more results" to load all posts
    console.log("\nLoading all posts...");
    for (let i = 0; i < 15; i++) {
      const clickResp = await send(
        "Runtime.evaluate",
        {
          expression: `(function() {
          const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Show more results'));
          if (btn) { btn.click(); return 'clicked'; }
          window.scrollTo(0, document.body.scrollHeight);
          return 'scrolled';
        })()`,
          returnByValue: true,
        },
        sessionId,
      );

      const action = clickResp.result?.result?.value || "unknown";
      console.log(`  Round ${i + 1}: ${action}`);
      await new Promise((r) => setTimeout(r, 3000));

      const checkResp = await send(
        "Runtime.evaluate",
        {
          expression: `(function() {
          const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Show more results'));
          return btn ? 'present' : 'gone';
        })()`,
          returnByValue: true,
        },
        sessionId,
      );

      if (checkResp.result?.result?.value === "gone") {
        console.log("  All posts loaded!");
        break;
      }
    }

    // Step 2: Extract posts using anchor-based approach
    console.log("\nExtracting posts...");
    const expression = `
      (function() {
        const out = { url: location.href, scrapedAt: new Date().toISOString(), posts: [] };
        const seen = new Set();

        // Find all anchors that link to activity posts
        const anchors = document.querySelectorAll('a[href*="/feed/update/urn:li:activity:"]');

        anchors.forEach(a => {
          // Extract activity ID from the href
          const href = a.getAttribute('href') || '';
          const m = href.match(/urn:li:activity:(\\d+)/);
          if (!m) return;
          const activityId = m[1];
          if (seen.has(activityId)) return;
          seen.add(activityId);

          // Walk up to find the post container
          // On the saved-posts page, the structure is different from the feed.
          // Each post is in a container that has the author info, timestamp, and text.
          let container = a;
          for (let i = 0; i < 10; i++) {
            if (!container.parentElement) break;
            container = container.parentElement;
            // Check if this container has a time element or author link
            if (container.querySelector('time') || container.querySelector('a[href*="/in/"]')) break;
          }

          // Timestamp
          const timeEl = container.querySelector('time');
          const datetime = timeEl ? timeEl.getAttribute('datetime') : null;
          const relative = timeEl ? timeEl.textContent.trim() : null;

          // Author
          const authorLink = container.querySelector('a[href*="/in/"]');
          const authorHref = authorLink ? authorLink.getAttribute('href') : null;
          let authorName = null;
          if (authorLink) {
            const nameSpan = authorLink.querySelector('span[aria-hidden="true"]') || authorLink;
            authorName = nameSpan ? nameSpan.textContent.trim() : authorLink.textContent.trim();
            // Clean up author name (remove trailing/leading whitespace and "•")
            if (authorName) authorName = authorName.replace(/^\\s+|\\s+$/g, '').replace(/•.*$/, '').trim();
          }

          // Post text - look for text content in the container
          // Try multiple selectors that might contain the post text
          const textEl = container.querySelector(
            '.feed-shared-update-v2__description, ' +
            '.update-components-text, ' +
            '[data-test-id="main-feed-activity-card__commentary"], ' +
            '.feed-shared-text, ' +
            '.update-components-update-v2__commentary, ' +
            '[class*="commentary"], ' +
            '[class*="description"]'
          );
          // If no specific text element found, try getting text from the container itself
          let text = '';
          if (textEl) {
            text = textEl.textContent.trim();
          } else {
            // Get all text nodes, excluding button/link text
            const clone = container.cloneNode(true);
            clone.querySelectorAll('button, a, time, img').forEach(el => el.remove());
            text = clone.textContent.trim();
          }

          // External links (GitHub etc.)
          const links = Array.from(container.querySelectorAll('a[href]'))
            .map(a => a.href)
            .filter(h => /^https?:\\/\\//.test(h) && !h.includes('linkedin.com'));

          // Post URL
          const postUrl = href.startsWith('http') ? href : 'https://www.linkedin.com' + href;

          out.posts.push({
            activityId,
            datetime,
            relative,
            authorName,
            authorHref: authorHref ? authorHref.split('?')[0] : null,
            text: text.slice(0, 2000),
            postUrl,
            externalLinks: [...new Set(links)]
          });
        });

        out.postCount = out.posts.length;
        return JSON.stringify(out);
      })()
    `;

    const evalResp = await send(
      "Runtime.evaluate",
      {
        expression,
        returnByValue: true,
        awaitPromise: true,
      },
      sessionId,
    );

    const rawValue = evalResp.result?.result?.value;
    if (!rawValue) {
      console.error(
        "Extraction failed:",
        JSON.stringify(evalResp.result, null, 2),
      );
      ws.close();
      process.exit(1);
    }

    const result =
      typeof rawValue === "string" ? JSON.parse(rawValue) : rawValue;

    fs.writeFileSync(
      "C:/Users/M316235/repo/research/linkedin-saved.json",
      JSON.stringify(result, null, 2),
    );
    console.log("\n=== SUCCESS! Scraped " + result.postCount + " posts ===");
    console.log("Saved to linkedin-saved.json");
    console.log("\nFirst 5 posts:");
    result.posts.slice(0, 5).forEach((p) => {
      console.log(
        "  " + (p.relative || p.datetime || "no date") + " | " + p.authorName,
      );
      console.log("    " + (p.text || "").slice(0, 120).replace(/\\s+/g, " "));
      if (p.externalLinks.length)
        console.log("    Links: " + p.externalLinks.slice(0, 3).join(", "));
    });

    ws.close();
  } catch (e) {
    console.error("ERROR:", e.message);
    console.error(e.stack);
    process.exit(1);
  }
})();
