#!/usr/bin/env node
/**
 * Parse a Chrome accessibility tree snapshot of a LinkedIn "Saved Posts" page
 * and extract structured post data to JSON.
 *
 * Usage:
 *   node scripts/parse-snapshot.mjs [inputPath] [outputPath]
 *
 * Defaults:
 *   inputPath  = data/snapshot.txt
 *   outputPath = data/posts.json
 */

import { readFileSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = resolve(__dirname, "..");

const inputPath = resolve(PROJECT_ROOT, process.argv[2] ?? "data/snapshot.txt");
const outputPath = resolve(PROJECT_ROOT, process.argv[3] ?? "data/posts.json");

// ---------------------------------------------------------------------------
// Regex patterns
// ---------------------------------------------------------------------------

// A line that declares a link to a LinkedIn profile, e.g.:
//   uid=1_60 link "Charly Wargnier" url="https://www.linkedin.com/in/ACoAA..."
const AUTHOR_LINK_RE =
  /link "([^"]+)" url="(https:\/\/www\.linkedin\.com\/in\/[^"]+)"/;

// The *name* author link is the one whose immediate child is a StaticText
// with the same name (the other link with the same URL wraps the profile photo).
// We detect "name" links by looking for the pattern where the next child line
// is a StaticText containing the author name. We handle this contextually.

// Timestamp like "16h •", "1d •", "2w •", "3mo •"
const TIMESTAMP_RE = /^(\d+(?:h|d|w|mo)) •$/;

// Post URL link — any link whose URL points at a feed/update activity.
// The link text varies: "Image preview", "View Video Image preview",
// or a long descriptive string when the post is an article/card share.
const POST_URL_RE =
  /link "[^"]*" url="(https:\/\/www\.linkedin\.com\/feed\/update\/urn:li:activity:(\d+))/;

// LinkedIn short link (lnkd.in)
const LNKD_IN_RE = /https:\/\/lnkd\.in\/[A-Za-z0-9_-]+/g;

// Activity ID extractor from a feed URL
const ACTIVITY_ID_RE = /urn:li:activity:(\d+)/;

// "Link in comments" detector — broad set of phrasings people use to say the
// real link is in the comments section rather than the post body. We match in
// both word orders (link-word ... comments OR comments ... link-word).
// [^.\n]* keeps the match within a single sentence/line so we don't span
// unrelated paragraphs.
const LINK_WORDS =
  "link|repo|github|code|video|guide|tutorial|paper|blog|docs?|invite|write-?up|installation|install|commands?|url|collection|thread|resource";
const LINK_IN_COMMENTS_RE = new RegExp(
  "\\b(" +
    LINK_WORDS +
    ")\\b[^.\\n]*\\b(comments?|replies?)\\b|" +
    "\\b(comments?|replies?)\\b[^.\\n]*\\b(" +
    LINK_WORDS +
    ")\\b",
  "i",
);

// ---------------------------------------------------------------------------
// Parsing
// ---------------------------------------------------------------------------

/**
 * Read the snapshot file and return an array of lines (preserving indentation).
 * @returns {string[]}
 */
function readSnapshotLines() {
  const raw = readFileSync(inputPath, "utf8");
  // Normalize CRLF -> LF and split.
  return raw.replace(/\r\n/g, "\n").split("\n");
}

/**
 * Extract the "uid=..." token from a line, if present.
 * @param {string} line
 * @returns {string | null}
 */
function extractUid(line) {
  const m = line.match(/uid=(\S+)/);
  return m ? m[1] : null;
}

/**
 * Get the leading-whitespace indentation (in spaces) of a line.
 * @param {string} line
 * @returns {number}
 */
function indentOf(line) {
  const m = line.match(/^[ \t]*/);
  return m ? m[0].length : 0;
}

/**
 * Try to parse a StaticText value from a line.
 * @param {string} line
 * @returns {string | null}
 */
function parseStaticText(line) {
  // Matches: StaticText "..."  (the value may contain escaped quotes)
  const m = line.match(/StaticText "((?:[^"\\]|\\.)*)"$/);
  if (!m) return null;
  // Unescape common escape sequences.
  return m[1].replace(/\\"/g, '"').replace(/\\n/g, "\n").replace(/\\\\/g, "\\");
}

/**
 * Determine whether a line is a link to a LinkedIn profile (/in/ URL).
 * Returns the link text and URL if matched.
 * @param {string} line
 * @returns {{text: string, url: string} | null}
 */
function parseAuthorLink(line) {
  const m = line.match(AUTHOR_LINK_RE);
  if (!m) return null;
  return { text: m[1], url: m[2] };
}

/**
 * Determine whether a line contains a post-URL link (Image preview / View Video
 * Image preview pointing at a feed/update activity URL).
 * @param {string} line
 * @returns {{url: string, activityId: string} | null}
 */
function parsePostUrlLink(line) {
  const m = line.match(POST_URL_RE);
  if (!m) return null;
  return { url: m[1], activityId: m[2] };
}

/**
 * Determine whether a line is a "name" author link — i.e. a profile /in/ link
 * whose *next* child line is a StaticText with the same name.
 *
 * In the a11y snapshot, each post has two consecutive links to the author's
 * profile:
 *   1. The profile photo (child = image "AuthorName")
 *   2. The name            (child = StaticText "AuthorName")
 *
 * Occasionally the photo link is missing or also has a StaticText child
 * (e.g. when the avatar failed to load), producing two consecutive name links
 * with the same text. In that case we treat the *second* one as the canonical
 * post boundary and return null for the first so the caller skips past it.
 *
 * @param {string[]} lines
 * @param {number} i
 * @returns {{name: string, url: string} | null}
 */
function parseNameAuthorLink(lines, i) {
  const link = parseAuthorLink(lines[i]);
  if (!link) return null;
  const myIndent = indentOf(lines[i]);

  // Inspect child lines (more indented) to decide if this is a name link.
  let hasNameChild = false;
  for (let j = i + 1; j < Math.min(i + 3, lines.length); j++) {
    const next = lines[j];
    if (!next || next.trim() === "") continue;
    if (indentOf(next) <= myIndent) break; // not a child
    const text = parseStaticText(next);
    if (text !== null && text.trim() === link.text.trim()) {
      hasNameChild = true;
    }
    if (/image "/.test(next)) return null; // photo link, not name link
  }
  if (!hasNameChild) return null;

  // Check if the next sibling (same indentation) is also an /in/ link with the
  // same name. If so, this is the first of a duplicate pair — skip it by
  // returning null so the caller advances to the canonical second link.
  for (let j = i + 1; j < Math.min(i + 4, lines.length); j++) {
    const next = lines[j];
    if (!next || next.trim() === "") continue;
    const nextIndent = indentOf(next);
    if (nextIndent > myIndent) continue; // still inside children
    if (nextIndent < myIndent) break; // left this level
    // Same indentation — check if it's another /in/ link with the same name.
    const nextLink = parseAuthorLink(next);
    if (nextLink && nextLink.text.trim() === link.text.trim()) {
      // Duplicate pair — this is the first, skip it.
      return null;
    }
    break;
  }

  return { name: link.text, url: link.url };
}

/**
 * Parse the snapshot into an array of post objects.
 * @param {string[]} lines
 * @returns {Array<object>}
 */
function parsePosts(lines) {
  const posts = [];

  // We walk the lines and detect post "headers" — the pair of author links
  // (photo + name) that introduces each saved post. After detecting a header
  // we scan forward to collect the timestamp, post URL, and body StaticText.
  let i = 0;
  const n = lines.length;

  while (i < n) {
    const line = lines[i];

    // Skip the generic duplicate/summary element (it re-states a post in one
    // long line and is followed by the real structured post).
    if (/generic ".*Click to take more actions/.test(line)) {
      i++;
      continue;
    }

    // Detect the *name* author link — this is the canonical post start marker.
    const author = parseNameAuthorLink(lines, i);
    if (!author) {
      i++;
      continue;
    }

    // We've found a post header. Scan forward to collect:
    //   - timestamp  (first StaticText matching X[h|d|w|mo] •)
    //   - postUrl    (first Image-preview link with an activity URL)
    //   - bodyText   (all StaticText from the post body)
    // We stop when we hit the next post's author link or the end of the file.
    let timestamp = null;
    let postUrl = null;
    let activityId = null;
    const bodyChunks = [];
    let sawActionBtn = false;

    // Start scanning from the line after the author name link.
    let j = i + 1;
    while (j < n) {
      const cur = lines[j];

      // Stop if we've reached the next post's header.
      // The next post starts with a profile-photo link whose child is an image
      // — but to keep things simple, we check for *any* /in/ link followed by a
      // matching name StaticText that is NOT the current author link.
      if (j > i) {
        const nextAuthor = parseNameAuthorLink(lines, j);
        if (nextAuthor) break;
      }

      // Skip generic summary elements.
      if (/generic ".*Click to take more actions/.test(cur)) {
        j++;
        continue;
      }

      // Timestamp.
      if (timestamp === null) {
        const text = parseStaticText(cur);
        if (text !== null) {
          const tm = text.match(TIMESTAMP_RE);
          if (tm) {
            timestamp = tm[1];
            j++;
            continue;
          }
        }
      }

      // Post URL link (Image preview / View Video Image preview).
      if (postUrl === null) {
        const urlLink = parsePostUrlLink(cur);
        if (urlLink) {
          postUrl = urlLink.url;
          activityId = urlLink.activityId;
          j++;
          continue;
        }
      }

      // Body StaticText — collect anything after we've seen the action button
      // OR after we've seen the Image preview link. This avoids collecting the
      // headline ("• 2nd", "Founder at ...") as body text.
      if (/button "Click to take more actions/.test(cur)) {
        sawActionBtn = true;
        j++;
        continue;
      }

      if (sawActionBtn || postUrl !== null) {
        const text = parseStaticText(cur);
        if (text !== null) {
          // Skip UI strings that aren't body content.
          const trimmed = text.trim();
          if (
            trimmed !== "" &&
            trimmed !== " " &&
            !/^(See more|Repost|Like|Comment|Share|Send|Save|Saved|Follow|Unfollow)/.test(
              trimmed,
            ) &&
            !/^\d+\s+(reactions?|comments?|reposts?)$/i.test(trimmed) &&
            !/^\d+\s+(reaction|comment|repost)/i.test(trimmed)
          ) {
            bodyChunks.push(text);
          }
        }
      }

      j++;
    }

    // Build the body text — join chunks with appropriate whitespace.
    const bodyText = bodyChunks.join("\n").trim();

    // Extract lnkd.in external links from the body text.
    const externalLinks = [];
    {
      const matches = bodyText.matchAll(LNKD_IN_RE);
      const seen = new Set();
      for (const m of matches) {
        if (!seen.has(m[0])) {
          seen.add(m[0]);
          externalLinks.push(m[0]);
        }
      }
    }

    // Detect "link in comments" flag.
    const linkInComments = LINK_IN_COMMENTS_RE.test(bodyText);

    // Fallback activity ID from URL if we found a URL but didn't capture the ID.
    if (!activityId && postUrl) {
      const m = postUrl.match(ACTIVITY_ID_RE);
      if (m) activityId = m[1];
    }

    posts.push({
      activityId: activityId ?? null,
      authorName: author.name,
      timestamp: timestamp ?? null,
      text: bodyText,
      postUrl: postUrl ?? null,
      externalLinks,
      linkInComments,
    });

    // Continue scanning from where we left off.
    i = j;
  }

  return posts;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
  console.log(`Reading snapshot from: ${inputPath}`);
  const lines = readSnapshotLines();
  console.log(`Snapshot has ${lines.length} lines`);

  const posts = parsePosts(lines);
  console.log(`Extracted ${posts.length} posts`);

  // Write JSON output.
  const json = JSON.stringify(posts, null, 2);
  writeFileSync(outputPath, json, "utf8");
  console.log(`Wrote JSON to: ${outputPath}`);

  // Summary stats.
  const withLinkInComments = posts.filter((p) => p.linkInComments).length;
  const withExternalLinks = posts.filter(
    (p) => p.externalLinks.length > 0,
  ).length;
  const withPostUrl = posts.filter((p) => p.postUrl !== null).length;
  const withTimestamp = posts.filter((p) => p.timestamp !== null).length;

  console.log("\n=== Summary ===");
  console.log(`Total posts:                ${posts.length}`);
  console.log(`Posts with postUrl:         ${withPostUrl}`);
  console.log(`Posts with timestamp:       ${withTimestamp}`);
  console.log(`Posts with external links:  ${withExternalLinks}`);
  console.log(`Posts with linkInComments:  ${withLinkInComments}`);

  console.log("\n=== First 5 posts (preview) ===");
  for (const p of posts.slice(0, 5)) {
    console.log(JSON.stringify(p, null, 2));
  }
}

main();
