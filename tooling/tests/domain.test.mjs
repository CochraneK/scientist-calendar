import assert from "node:assert/strict";
import test from "node:test";

import {
  getDateKey,
  getDaysInMonth,
  getNextMonth,
  getPreviousMonth,
  getScientistForDate,
  groupScientistsByDate,
  resolveCalendarDate,
} from "../../src/domain/calendar.ts";
import {
  SITE_BASE_PATH,
  SITE_ORIGIN,
  scientistAbsoluteUrl,
  scientistBrowserPath,
  scientistIdFromPath,
  scientistPath,
} from "../../src/domain/scientistRoutes.ts";

test("resolveCalendarDate maps leap day (2/29) to 2/28 and preserves normal dates", () => {
  assert.deepEqual(resolveCalendarDate({ year: 2024, month: 2, day: 29 }), {
    date: { year: 2024, month: 2, day: 28 },
    isLeapDay: true,
  });

  assert.deepEqual(resolveCalendarDate({ year: 2024, month: 2, day: 28 }), {
    date: { year: 2024, month: 2, day: 28 },
    isLeapDay: false,
  });

  assert.deepEqual(resolveCalendarDate({ year: 2026, month: 11, day: 23 }), {
    date: { year: 2026, month: 11, day: 23 },
    isLeapDay: false,
  });
});

test("getDaysInMonth handles common years, leap years, and century rules", () => {
  assert.equal(getDaysInMonth(2026, 2), 28);
  assert.equal(getDaysInMonth(2024, 2), 29);
  assert.equal(getDaysInMonth(2000, 2), 29);
  assert.equal(getDaysInMonth(1900, 2), 28);
  assert.equal(getDaysInMonth(2100, 2), 28);
  assert.equal(getDaysInMonth(2026, 1), 31);
  assert.equal(getDaysInMonth(2026, 4), 30);
  assert.equal(getDaysInMonth(2026, 12), 31);
});

test("getScientistForDate returns exact date match, falls back 2/29 -> 2/28, and avoids silent fallback", () => {
  const sample = [
    { id: "pauling", month: 2, day: 28 },
    { id: "einstein", month: 3, day: 14 },
  ];

  assert.equal(getScientistForDate(sample, { year: 2026, month: 3, day: 14 })?.id, "einstein");
  assert.equal(getScientistForDate(sample, { year: 2024, month: 2, day: 29 })?.id, "pauling");
  assert.equal(getScientistForDate(sample, { year: 2026, month: 7, day: 1 }), undefined);
});

test("groupScientistsByDate groups multi-scientist dates under month*100+day preserving order", () => {
  const sample = [
    { id: "a", month: 3, day: 14 },
    { id: "b", month: 3, day: 14 },
    { id: "c", month: 12, day: 25 },
  ];

  const grouped = groupScientistsByDate(sample);
  assert.deepEqual(
    grouped.get(314)?.map((item) => item.id),
    ["a", "b"],
  );
  assert.deepEqual(
    grouped.get(1225)?.map((item) => item.id),
    ["c"],
  );
  assert.equal(grouped.get(101), undefined);
});

test("month navigation wraps cleanly across year boundary and getDateKey formats M/D", () => {
  assert.equal(getPreviousMonth(1), 12);
  assert.equal(getPreviousMonth(6), 5);
  assert.equal(getNextMonth(12), 1);
  assert.equal(getNextMonth(6), 7);
  assert.equal(getDateKey(3, 14), "3/14");
});

test("scientistRoutes builds and parses relative, browser, and absolute scientist paths", () => {
  assert.equal(scientistPath("auto-q935"), `${SITE_BASE_PATH}/scientists/auto-q935/`);
  assert.equal(scientistPath("auto-q935", ""), "/scientists/auto-q935/");
  assert.equal(scientistPath("auto-q935", "/"), "/scientists/auto-q935/");
  assert.equal(scientistPath("auto-q935", "custom/base/"), "/custom/base/scientists/auto-q935/");
  assert.equal(
    scientistAbsoluteUrl("marie-curie"),
    `${SITE_ORIGIN}${SITE_BASE_PATH}/scientists/marie-curie/`,
  );

  assert.equal(
    scientistBrowserPath("newton", `${SITE_BASE_PATH}/scientists/einstein/`),
    `${SITE_BASE_PATH}/scientists/newton/`,
  );
  assert.equal(scientistBrowserPath("newton", "/"), "/scientists/newton/");

  assert.equal(scientistIdFromPath(`${SITE_BASE_PATH}/scientists/marie-curie/`), "marie-curie");
  assert.equal(scientistIdFromPath("/scientists/id%20with%20space/"), "id with space");
  assert.equal(scientistIdFromPath("/scientists/%E0%A4%A/"), null);
  assert.equal(scientistIdFromPath("/scientist-calendar/"), null);
});
