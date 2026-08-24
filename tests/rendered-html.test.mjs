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

test("server-renders the calendar page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>科学家日历｜每天认识一位科学家<\/title>/);
  assert.match(html, /今日人物/);
  assert.match(html, /位人物档案/);
  assert.match(html, /从好奇出发/);
  assert.match(html, /print\/科学家日历_精选466位_A4打印版\.pdf/);
});

test("calendar dataset stays consistent", async () => {
  const [scientists, manifest, quotes] = await Promise.all([
    readFile(new URL("../app/scientists.json", import.meta.url), "utf8").then(JSON.parse),
    readFile(new URL("../public/avatars.json", import.meta.url), "utf8").then(JSON.parse),
    readFile(new URL("../app/quotes.json", import.meta.url), "utf8").then(JSON.parse),
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
