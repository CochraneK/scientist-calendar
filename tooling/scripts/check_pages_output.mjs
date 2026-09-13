import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const repoRoot = resolve(import.meta.dirname, "../..");
const docsDir = resolve(repoRoot, "docs");
const scientists = JSON.parse(readFileSync(resolve(repoRoot, "app/data/scientists-index.json"), "utf8"));
const siteRoot = "https://cochranek.github.io/scientist-calendar/";

const rootHtml = readFileSync(resolve(docsDir, "index.html"), "utf8");
assert.match(rootHtml, new RegExp(`<link[^>]+rel="canonical"[^>]+href="${siteRoot.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}"`));

for (const scientist of scientists) {
  const profilePath = resolve(docsDir, "scientists", encodeURIComponent(scientist.id), "index.html");
  assert.equal(existsSync(profilePath), true, `missing profile page for ${scientist.id}`);
  const html = readFileSync(profilePath, "utf8");
  const canonical = `${siteRoot}scientists/${encodeURIComponent(scientist.id)}/`;
  assert.ok(html.includes(`<title>${scientist.name}｜科学家日历</title>`), `wrong title for ${scientist.id}`);
  assert.ok(html.includes(`href="${canonical}"`), `missing canonical for ${scientist.id}`);
  assert.ok(html.includes(`content="${canonical}"`), `missing og:url for ${scientist.id}`);
  assert.ok(html.includes('"@type":"Person"'), `missing Person structured data for ${scientist.id}`);
}

const sitemapPath = resolve(docsDir, "sitemap.xml");
assert.equal(existsSync(sitemapPath), true, "missing sitemap.xml");
const sitemap = readFileSync(sitemapPath, "utf8");
assert.ok(sitemap.includes(`<loc>${siteRoot}</loc>`), "sitemap missing site root");
for (const scientist of scientists) {
  const url = `${siteRoot}scientists/${encodeURIComponent(scientist.id)}/`;
  assert.ok(sitemap.includes(`<loc>${url}</loc>`), `sitemap missing ${scientist.id}`);
}

console.log(`✓ Pages output verified: ${scientists.length} scientist profiles + sitemap`);
