// scripts/clean-data.mjs
//
// Cleans up scraped LinkedIn "saved posts" data produced by
// chrome_research_evaluate_script (saved to data/posts-full.json).
//
// What it does:
//   1. Reads data/posts-full.json
//   2. Cleans author names — LinkedIn shows "Status is offline" as the link
//      text; the real name lives in the avatar img's alt attribute, which the
//      extractor reads. We strip any remaining status remnants and whitespace.
//   3. Writes cleaned data to data/posts-cleaned.json
//   4. Prints stats: total posts, GitHub links, linkInComments, etc.
//
// Run with:  node scripts/clean-data.mjs

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..");

const INPUT = path.join(ROOT, "data", "posts-full.json");
const OUTPUT = path.join(ROOT, "data", "posts-cleaned.json");

// Clean a URL: trim trailing word characters that got concatenated by textContent.
// lnkd.in short links have exactly 8 alphanumeric chars in the path.
function cleanUrl(url) {
  let u = url.trim();
  // lnkd.in: keep only the 8-char path (e.g. https://lnkd.in/erUuKhyc)
  const lnkdMatch = u.match(/^(https:\/\/lnkd\.in\/[a-zA-Z0-9_-]{8})/);
  if (lnkdMatch) return lnkdMatch[1];
  // General: strip trailing punctuation that isn't part of a URL
  u = u.replace(/[.,;:!?)\]>]+$/, "");
  return u;
}

// Clean an author name. Handles "Status is offline" leftovers and stray bullets.
function cleanAuthor(author) {
  if (author == null) return null;
  let name = String(author).trim();
  if (!name) return null;
  // Strip "Status is offline" remnants (the real name sits next to it)
  name = name.replace(/Status is offline/gi, "").trim();
  // Strip leading bullets / separators LinkedIn sometimes inserts
  name = name
    .replace(/^•\s*/, "")
    .replace(/^\|\s*/, "")
    .trim();
  // Collapse internal whitespace
  name = name.replace(/\s+/g, " ");
  // If the field was ONLY "Status is offline", there's nothing left
  if (!name || name.length < 2) return null;
  // Cap absurd lengths
  if (name.length > 120) name = name.slice(0, 120);
  return name;
}

function main() {
  if (!fs.existsSync(INPUT)) {
    console.error(`Input not found: ${INPUT}`);
    console.error("Run the evaluate_script with filePath to produce it first.");
    process.exit(1);
  }

  const raw = fs.readFileSync(INPUT, "utf8");
  const data = JSON.parse(raw);
  const posts = Array.isArray(data) ? data : data.posts || [];

  let fixedCount = 0;
  const cleaned = posts.map((p) => {
    const before = p.author;
    const author = cleanAuthor(p.author);
    if (author !== before) fixedCount++;
    const links = (p.links || []).map(cleanUrl);
    // Deduplicate after cleaning
    const seen = new Set();
    const dedupedLinks = links.filter((l) => {
      if (seen.has(l)) return false;
      seen.add(l);
      return true;
    });
    return { ...p, author, links: dedupedLinks };
  });

  const out = {
    total: cleaned.length,
    scrapedAt: data.scrapedAt || null,
    url: data.url || null,
    cleanedAt: new Date().toISOString(),
    posts: cleaned,
  };

  fs.writeFileSync(OUTPUT, JSON.stringify(out, null, 2), "utf8");

  // ---- Stats ----
  const withAnyLink = cleaned.filter((p) => (p.links || []).length > 0);
  const withGitHub = cleaned.filter((p) =>
    (p.links || []).some((l) => /github\.com/i.test(l)),
  );
  const withLnkd = cleaned.filter((p) =>
    (p.links || []).some((l) => /lnkd\.in/i.test(l)),
  );
  const withLinkInComments = cleaned.filter((p) => p.linkInComments === true);
  const withMissingAuthor = cleaned.filter((p) => !p.author);

  const githubLinks = new Set();
  for (const p of cleaned) {
    for (const l of p.links || []) {
      if (/github\.com/i.test(l)) githubLinks.add(l);
    }
  }

  console.log("=== LinkedIn Saved Posts — Cleaned ===");
  console.log(`Input:                   ${INPUT}`);
  console.log(`Output:                  ${OUTPUT}`);
  console.log(`Total posts:             ${cleaned.length}`);
  console.log(`Authors fixed:           ${fixedCount}`);
  console.log(`Posts w/ missing author: ${withMissingAuthor.length}`);
  console.log(`Posts w/ any link:       ${withAnyLink.length}`);
  console.log(`Posts w/ GitHub link:    ${withGitHub.length}`);
  console.log(`Posts w/ lnkd.in link:   ${withLnkd.length}`);
  console.log(`Posts w/ linkInComments: ${withLinkInComments.length}`);
  console.log(`Unique GitHub URLs:      ${githubLinks.size}`);

  if (withGitHub.length) {
    console.log("\nSample GitHub links:");
    [...githubLinks].slice(0, 10).forEach((l) => console.log(`  ${l}`));
  }

  // Sample of cleaned posts so we can eyeball author name recovery
  console.log("\nFirst 5 posts (author | ts | links): ");
  cleaned.slice(0, 5).forEach((p) => {
    console.log(
      `  ${p.author || "(no author)"} | ${p.ts || "(no ts)"} | ${(p.links || []).length} link(s)`,
    );
  });
}

main();
