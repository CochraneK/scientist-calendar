#!/usr/bin/env python3
"""生成 365 天年度科学家日历订阅文件（RFC 5545 .ics）。

用法：
  python -X utf8 tooling/scripts/generate_ics_calendar.py          # 生成 public/scientist-calendar.ics
  python -X utf8 tooling/scripts/generate_ics_calendar.py --check  # 校验现有 .ics 与数据一致（CI 用）

特点：
  - 严格覆盖平年 365 天（1/1 – 12/31），按年循环（RRULE:FREQ=YEARLY），导入 Apple/Google/Outlook
    或手机日历后每年自动提醒，无需按年重新导入；
  - 同日有多位科学家时合并到同一条当日全天事件，正文列出每位人物的简介、名言与永久链接；
  - 确定性输出（固定 DTSTAMP），保证 `--check` 在本地与 CI 下逐字节可重复校验；
  - 严格按 RFC 5545 规则转义文本并做 75 字节（UTF-8 octets）安全折行。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "app" / "data" / "scientists.json"
QUOTES_FILE = ROOT / "app" / "data" / "quotes.json"
OUT_FILE = ROOT / "public" / "scientist-calendar.ics"

SITE_ORIGIN = "https://cochranek.github.io"
SITE_BASE = "/scientist-calendar"
BASE_YEAR = 2026  # 平年基准（365 天）
FIXED_DTSTAMP = "20260101T000000Z"


def ics_escape(text: str) -> str:
    """按 RFC 5545 §3.3.11 转义 TEXT 属性中的特殊字符。"""
    return (
        text.replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def fold_ics_line(line: str, max_octets: int = 75) -> str:
    """按 RFC 5545 §3.1 将单行折行为不超过 75 UTF-8 字节的逻辑行（绝不截断多字节字符）。"""
    encoded = line.encode("utf-8")
    if len(encoded) <= max_octets:
        return line

    parts: list[str] = []
    cur: list[str] = []
    cur_bytes = 0
    limit = max_octets
    for ch in line:
        ch_bytes = len(ch.encode("utf-8"))
        if cur and cur_bytes + ch_bytes > limit:
            parts.append("".join(cur))
            cur = [ch]
            cur_bytes = ch_bytes
            limit = max_octets - 1  # 续行前导空格占 1 字节
        else:
            cur.append(ch)
            cur_bytes += ch_bytes
    if cur:
        parts.append("".join(cur))
    return "\r\n ".join(parts)


def scientist_url(scientist_id: str) -> str:
    return f"{SITE_ORIGIN}{SITE_BASE}/scientists/{urllib.parse.quote(scientist_id, safe='')}/"


def build_ics(scientists: list[dict], quotes: dict[str, dict]) -> str:
    by_day: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for item in scientists:
        by_day[(int(item["month"]), int(item["day"]))].append(item)

    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Scientist Calendar//Daily Scientists 365//ZH",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:科学家日历｜每天认识一位科学家",
        "X-WR-CALDESC:365 天科学人物日历：每天认识一位科学家、一项发现与一个改变世界的念头。",
    ]

    day = dt.date(BASE_YEAR, 1, 1)
    end_day = dt.date(BASE_YEAR, 12, 31)
    event_count = 0

    while day <= end_day:
        entries = by_day.get((day.month, day.day), [])
        if not entries:
            raise RuntimeError(f"缺少 {day.month}/{day.day} 的科学家条目，无法生成完整 365 天日历")

        primary = entries[0]
        if len(entries) == 1:
            summary = f"今日科学家：{primary['name']}（{primary['field']}）"
        else:
            summary = f"今日科学家：{primary['name']} 等 {len(entries)} 位"

        desc_blocks: list[str] = []
        for idx, s in enumerate(entries, start=1):
            prefix = f"[{idx}/{len(entries)}] " if len(entries) > 1 else ""
            block_lines = [
                f"{prefix}{s['name']}（{s['latinName']} · {s['years']}）",
                f"{s['country']} · {s['field']} · {s['relation']}",
                f"阅读线索：{s['tagline']}",
                f"核心贡献：{s['contribution']}",
            ]
            q = quotes.get(s["id"])
            if q and q.get("text"):
                q_text = q["text"].strip()
                q_src = q.get("source", "").strip()
                block_lines.append(f"引语：“{q_text}”" + (f" — {q_src}" if q_src else ""))
            block_lines.append(f"人物档案：{scientist_url(s['id'])}")
            desc_blocks.append("\n".join(block_lines))

        description = "\n\n".join(desc_blocks)
        next_day = day + dt.timedelta(days=1)
        uid = f"scientist-calendar-{day.month:02d}{day.day:02d}@cochranek.github.io"
        categories = ",".join(dict.fromkeys(["科学家日历", *(s["field"] for s in entries)]))

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{FIXED_DTSTAMP}",
            f"DTSTART;VALUE=DATE:{day.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{next_day.strftime('%Y%m%d')}",
            "RRULE:FREQ=YEARLY",
            f"SUMMARY:{ics_escape(summary)}",
            f"DESCRIPTION:{ics_escape(description)}",
            f"URL:{scientist_url(primary['id'])}",
            f"CATEGORIES:{ics_escape(categories)}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ])
        event_count += 1
        day = next_day

    if event_count != 365:
        raise RuntimeError(f"期望 365 条全天事件，实际生成 {event_count} 条")

    lines.append("END:VCALENDAR")
    folded = [fold_ics_line(ln) for ln in lines]
    return "\r\n".join(folded) + "\r\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="生成或校验 365 天科学家日历 .ics 订阅文件")
    parser.add_argument("--check", action="store_true", help="只检查现有文件是否最新，不写入")
    args = parser.parse_args()

    scientists = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    quotes = json.loads(QUOTES_FILE.read_text(encoding="utf-8"))
    content = build_ics(scientists, quotes)

    if args.check:
        if not OUT_FILE.exists():
            print(f"✗ 缺少订阅文件：{OUT_FILE.relative_to(ROOT)}", file=sys.stderr)
            return 1
        existing = OUT_FILE.read_bytes().decode("utf-8")
        if existing != content:
            print(
                f"✗ {OUT_FILE.relative_to(ROOT)} 与当前数据不一致，请运行 npm run build:ics 重新生成",
                file=sys.stderr,
            )
            return 1
        print(f"✓ {OUT_FILE.relative_to(ROOT)} 校验通过（365 条年度循环事件）")
        return 0

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_bytes(content.encode("utf-8"))
    print(f"✓ 已生成 {OUT_FILE.relative_to(ROOT)}（{len(content.encode('utf-8')):,} bytes，365 条年度循环事件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
