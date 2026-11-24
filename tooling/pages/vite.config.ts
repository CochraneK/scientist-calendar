import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath, URL } from "node:url";
import { SITE_URL, scientistAbsoluteUrl } from "../../src/domain/scientistRoutes.ts";
import { SITE_CONFIG, entryTitle } from "../../src/domain/siteConfig.ts";

type ScientistSeo = {
  id: string;
  name: string;
  latinName: string;
  field: string;
  country: string;
  contribution: string;
  tagline: string;
  month: number;
  day: number;
};

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function setAttribute(html: string, tagPattern: RegExp, attribute: "content" | "href", value: string): string {
  let matched = false;
  const next = html.replace(tagPattern, (tag) => {
    matched = true;
    const attributePattern = new RegExp(`${attribute}="[^"]*"`, "i");
    if (!attributePattern.test(tag)) throw new Error(`Missing ${attribute} on SEO tag: ${tag}`);
    return tag.replace(attributePattern, `${attribute}="${escapeHtml(value)}"`);
  });
  if (!matched) throw new Error(`Missing SEO tag matching ${tagPattern}`);
  return next;
}

function scientistDescription(scientist: ScientistSeo): string {
  const description = `${scientist.name}（${scientist.latinName}）｜${scientist.country} · ${scientist.field}｜${scientist.tagline}。核心贡献：${scientist.contribution}`;
  return description.length > 170 ? `${description.slice(0, 167)}…` : description;
}

function renderScientistHtml(baseHtml: string, scientist: ScientistSeo): string {
  const title = entryTitle(scientist.name);
  const description = scientistDescription(scientist);
  const canonical = scientistAbsoluteUrl(scientist.id);

  let html = baseHtml.replace(/<title>[^<]*<\/title>/i, `<title>${escapeHtml(title)}</title>`);
  html = setAttribute(html, /<meta[^>]+name="description"[^>]*>/i, "content", description);
  html = setAttribute(html, /<meta[^>]+property="og:title"[^>]*>/i, "content", title);
  html = setAttribute(html, /<meta[^>]+property="og:description"[^>]*>/i, "content", description);
  html = setAttribute(html, /<meta[^>]+property="og:url"[^>]*>/i, "content", canonical);
  html = setAttribute(html, /<meta[^>]+property="og:type"[^>]*>/i, "content", "profile");
  html = setAttribute(html, /<meta[^>]+name="twitter:title"[^>]*>/i, "content", title);
  html = setAttribute(html, /<meta[^>]+name="twitter:description"[^>]*>/i, "content", description);
  html = setAttribute(html, /<link[^>]+rel="canonical"[^>]*>/i, "href", canonical);

  const structuredData = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "Person",
    name: scientist.name,
    alternateName: scientist.latinName,
    description,
    url: canonical,
  }).replaceAll("<", "\\u003c");

  return html.replace("</head>", `    <script type="application/ld+json">${structuredData}</script>\n  </head>`);
}

// 静态站额外文件 + 466 个可直接访问的人物永久页。
function generateStaticPages() {
  return {
    name: "generate-static-scientist-pages",
    closeBundle() {
      const outDir = fileURLToPath(new URL("../../docs", import.meta.url));
      const indexPath = join(outDir, "index.html");
      let baseHtml = readFileSync(indexPath, "utf8");

      // 主题化 head 标签（title / meta / canonical / og:*），换学科 = 换 theme.json
      const siteTitle = `${SITE_CONFIG.name}｜${SITE_CONFIG.unitLabel.replace(/^位/, "每天认识一位")}`;
      const siteUrl = `${SITE_CONFIG.origin}${SITE_CONFIG.basePath}/`;
      const siteDesc = SITE_CONFIG.description;
      const ogImage = `${siteUrl}og.jpg`;
      baseHtml = baseHtml.replace(/<title>[^<]*<\/title>/, `<title>${escapeHtml(siteTitle)}</title>`);
      baseHtml = baseHtml.replace(/<link rel="icon"[^>]*href="[^"]*"/, `<link rel="icon" type="image/svg+xml" href="${SITE_CONFIG.basePath}/favicon.svg"`);
      baseHtml = baseHtml.replace(/<link rel="canonical"[^>]*href="[^"]*"/, `<link rel="canonical" href="${siteUrl}"`);
      baseHtml = baseHtml.replace(/<meta name="description" content="[^"]*"/, `<meta name="description" content="${escapeHtml(siteDesc)}"`);
      baseHtml = baseHtml.replace(/<meta property="og:title" content="[^"]*"/, `<meta property="og:title" content="${escapeHtml(siteTitle)}"`);
      baseHtml = baseHtml.replace(/<meta property="og:description" content="[^"]*"/, `<meta property="og:description" content="${escapeHtml(siteDesc)}"`);
      baseHtml = baseHtml.replace(/<meta property="og:image" content="[^"]*"/, `<meta property="og:image" content="${ogImage}"`);
      baseHtml = baseHtml.replace(/<meta property="og:url" content="[^"]*"/, `<meta property="og:url" content="${siteUrl}"`);
      baseHtml = baseHtml.replace(/<meta property="og:site_name" content="[^"]*"/, `<meta property="og:site_name" content="${escapeHtml(SITE_CONFIG.name)}"`);
      baseHtml = baseHtml.replace(/<meta name="twitter:title" content="[^"]*"/, `<meta name="twitter:title" content="${escapeHtml(siteTitle)}"`);
      baseHtml = baseHtml.replace(/<meta name="twitter:description" content="[^"]*"/, `<meta name="twitter:description" content="${escapeHtml(siteDesc)}"`);
      baseHtml = baseHtml.replace(/<meta name="twitter:image" content="[^"]*"/, `<meta name="twitter:image" content="${ogImage}"`);
      writeFileSync(indexPath, baseHtml, "utf8");
      const scientists = JSON.parse(
        readFileSync(new URL("../../app/data/scientists-index.json", import.meta.url), "utf8"),
      ) as ScientistSeo[];

      for (const scientist of scientists) {
        const directory = join(outDir, "scientists", encodeURIComponent(scientist.id));
        mkdirSync(directory, { recursive: true });
        writeFileSync(join(directory, "index.html"), renderScientistHtml(baseHtml, scientist), "utf8");
      }

      const urls = [SITE_URL, ...scientists.map((scientist) => scientistAbsoluteUrl(scientist.id))];
      const sitemap = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ...urls.map((url) => `  <url><loc>${escapeHtml(url)}</loc></url>`),
        "</urlset>",
        "",
      ].join("\n");
      writeFileSync(join(outDir, "sitemap.xml"), sitemap, "utf8");

      for (const name of ["backup-candidates.md"]) {
        copyFileSync(new URL(`./extras/${name}`, import.meta.url), join(outDir, name));
      }
    },
  };
}

export default defineConfig({
  root: fileURLToPath(new URL(".", import.meta.url)),
  base: `${SITE_CONFIG.basePath}/`,
  publicDir: "../../public",
  plugins: [react(), generateStaticPages()],
  build: {
    outDir: "../../docs",
    emptyOutDir: true,
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            {
              name: "vendor",
              test: /node_modules/,
            },
          ],
        },
      },
    },
  },
});
