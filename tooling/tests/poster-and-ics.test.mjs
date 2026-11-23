import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { posterFilename, wrapTextLines } from "../../src/lib/posterCanvas.ts";

const REPO_ROOT = new URL("../../", import.meta.url);

// 简单宽度测量器：ASCII 字符占 10px，宽字符占 20px
const approxWidth = (sample) =>
  [...sample].reduce((sum, ch) => sum + (ch.charCodeAt(0) < 128 ? 10 : 20), 0);

test("wrapTextLines wraps CJK and mixed Latin text without splitting words and appends ellipsis on overflow", () => {
  const cjk = wrapTextLines("科学并非一串遥远的姓名与年份，而是一代代人对世界的耐心注视。", 160, approxWidth, 4);
  assert.ok(cjk.length >= 2 && cjk.length <= 4);
  for (const line of cjk) {
    assert.ok(approxWidth(line) <= 160, `line overflowed: ${line}`);
  }

  const mixed = wrapTextLines("Albert Einstein proposed general relativity in 1915.", 160, approxWidth, 5);
  assert.ok(!mixed.some((line) => line.endsWith("Ein") || line.startsWith("stein")), "should not split Latin word");

  const truncated = wrapTextLines("一二三四五六七八九十一二三四五六七八九十", 100, approxWidth, 2);
  assert.equal(truncated.length, 2);
  assert.ok(truncated[1].endsWith("…"), `expected ellipsis on truncated line, got: ${truncated[1]}`);
});

test("posterFilename formats MMDD and strips unsafe filename characters", () => {
  const filename = posterFilename({
    id: "einstein",
    month: 3,
    day: 14,
    name: "阿尔伯特·爱因斯坦",
    latinName: "Albert Einstein",
    years: "1879–1955",
    field: "物理",
    country: "德国/美国",
    color: "blue",
    relation: "相对论",
    tagline: "",
    contribution: "",
  });
  assert.equal(filename, "科学家日历_0314_阿尔伯特·爱因斯坦.png");
});

test("generated scientist-calendar.ics conforms to RFC 5545 and covers all 365 days", async () => {
  const raw = await readFile(new URL("public/scientist-calendar.ics", REPO_ROOT), "utf8");
  assert.ok(raw.startsWith("BEGIN:VCALENDAR\r\n"), "ICS must start with BEGIN:VCALENDAR + CRLF");
  assert.ok(raw.endsWith("END:VCALENDAR\r\n"), "ICS must end with END:VCALENDAR + CRLF");

  // RFC 5545 §3.1: every folded line must be <= 75 UTF-8 octets (excluding CRLF)
  const rawLines = raw.split("\r\n");
  for (const line of rawLines) {
    const octets = Buffer.byteLength(line, "utf8");
    assert.ok(octets <= 75, `ICS line exceeded 75 octets (${octets}): ${line}`);
  }

  // Unfold lines and verify 365 unique MMDD events with yearly recurrence
  const unfolded = raw.replace(/\r\n[ \t]/g, "");
  const dtstarts = [...unfolded.matchAll(/^DTSTART;VALUE=DATE:2026(\d{4})$/gm)].map((m) => m[1]);
  assert.equal(dtstarts.length, 365, `expected 365 DTSTART entries, got ${dtstarts.length}`);
  assert.equal(new Set(dtstarts).size, 365, "all 365 days must be unique");

  const rrules = unfolded.match(/^RRULE:FREQ=YEARLY$/gm) ?? [];
  assert.equal(rrules.length, 365, "every VEVENT must recur yearly");
});
