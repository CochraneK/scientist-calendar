import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

// 中文行文里不该出现的半角标点（前后都是中日韩字符时即为排版错误）。
const HALFWIDTH_IN_CJK = /[一-鿿][,;:?!]|[一-鿿]\(/;

async function loadJson(relativePath) {
  return JSON.parse(await readFile(new URL(relativePath, import.meta.url), "utf8"));
}

test("server-renders the calendar page", async () => {
  const [response, scientists] = await Promise.all([
    render(),
    loadJson("../app/data/scientists.json"),
  ]);
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>科学家日历｜每天认识一位科学家<\/title>/);
  assert.match(html, /今日人物/);
  assert.match(html, /位人物档案/);
  assert.match(html, /从好奇出发/);

  // 打印版链接由数据推导，这里同样按数据推导，避免增删人物后测试失效。
  const pdfName = `print/科学家日历_精选${scientists.length}位_A4打印版.pdf`;
  assert.ok(html.includes(pdfName), `页面未出现打印版链接：${pdfName}`);
});

test("calendar dataset stays consistent", async () => {
  const [scientists, manifest, quotes] = await Promise.all([
    loadJson("../app/data/scientists.json"),
    loadJson("../public/avatars.json"),
    loadJson("../app/data/quotes.json"),
  ]);

  const ids = new Set(scientists.map((entry) => entry.id));
  assert.equal(ids.size, scientists.length, "scientist ids must be unique");

  const days = new Set(scientists.map((entry) => `${entry.month}-${entry.day}`));
  assert.equal(days.size, 365, "calendar should cover all 365 days");

  for (const [id, info] of Object.entries(manifest)) {
    assert.ok(ids.has(id), `avatar manifest references unknown scientist: ${id}`);
    if (info.photo) {
      await assert.doesNotReject(
        readFile(new URL(`../public/avatars/${id}.jpg`, import.meta.url)),
        `manifest says ${id} has a photo but public/avatars/${id}.jpg is missing`,
      );
    }
  }

  for (const id of Object.keys(quotes)) {
    assert.ok(ids.has(id), `quotes.json references unknown scientist: ${id}`);
  }
});

test("prose uses full-width punctuation", async () => {
  const [scientists, quotes] = await Promise.all([
    loadJson("../app/data/scientists.json"),
    loadJson("../app/data/quotes.json"),
  ]);

  const textFields = ["name", "country", "relation", "tagline", "story", "contribution", "fact"];
  for (const entry of scientists) {
    for (const field of textFields) {
      const value = entry[field];
      if (typeof value !== "string") continue;
      assert.ok(
        !HALFWIDTH_IN_CJK.test(value),
        `${entry.id}/${field} 中文语境出现半角标点：${value}`,
      );
    }
  }

  for (const [id, payload] of Object.entries(quotes)) {
    for (const field of ["text", "source"]) {
      const value = payload[field];
      if (typeof value !== "string") continue;
      assert.ok(
        !HALFWIDTH_IN_CJK.test(value),
        `quotes[${id}]/${field} 中文语境出现半角标点：${value}`,
      );
    }
  }
});
