import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath, URL } from "node:url";
import { SITE_URL, scientistAbsoluteUrl } from "../../src/domain/scientistRoutes.ts";

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
  const title = `${scientist.name}｜科学家日历`;
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
      const baseHtml = readFileSync(indexPath, "utf8");
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
  base: "/scientist-calendar/",
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
