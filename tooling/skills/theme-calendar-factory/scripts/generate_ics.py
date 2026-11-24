#!/usr/bin/env python3
"""主题日历通用 RFC 5545 订阅日历 (.ics) 生成器。

用法：
  python generate_ics.py --config theme.json [--out output/theme.ics] [--check]

特点：
  - 完全由 theme.json 驱动，换主题不改代码；
  - 同一日期有多位人物时自动合并为单条全天年度循环事件（RRULE:FREQ=YEARLY）；
  - 严格遵守 RFC 5545 §3.1：UTF-8 75 字节折行 + CRLF 行尾，兼容 Apple / Google / Outlook / 飞书日历。
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE_YEAR = 2026  # 平年基准年，用于生成跨年循环的 VALUE=DATE 事件


def resolve_cfg_path(cfg_path: Path, raw: str, *, prefer_config_dir: bool = False) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    from_cfg = (cfg_path.parent / p).resolve()
    if prefer_config_dir or from_cfg.exists():
        return from_cfg
    return p


def ics_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
    )


def fold_line(line: str, max_octets: int = 75) -> list[str]:
    """RFC 5545 §3.1: 按 UTF-8 字节数折行，绝不切断多字节中文字符。"""
    if len(line.encode("utf-8")) <= max_octets:
        return [line]
    out: list[str] = []
    cur = ""
    limit = max_octets
    for ch in line:
        cand = cur + ch
        if len(cand.encode("utf-8")) > limit:
            out.append(cur)
            cur = " " + ch
            limit = max_octets
        else:
            cur = cand
    if cur:
        out.append(cur)
    return out


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "theme-calendar"


def build_ics(cfg: dict, entries: list[dict], quotes: dict) -> str:
    theme = cfg.get("theme", {})
    fm = cfg["fieldMap"]
    theme_name = theme.get("name", "主题日历")
    theme_en = theme.get("nameEn", "Theme Calendar")
    unit_label = theme.get("unitLabel", "位人物")
    slug = slugify(theme_en)

    def get_field(entry: dict, role: str) -> str:
        key = fm.get(role)
        return str(entry.get(key, "") or "").strip() if key else ""

    by_date: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for entry in entries:
        by_date[(int(entry[fm["month"]]), int(entry[fm["day"]]))].append(entry)

    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//{theme_en}//Theme Calendar Factory//ZH",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{ics_escape(theme_name)}",
        f"X-WR-CALDESC:{ics_escape(f'{theme_name}：每天认识一{unit_label}')}",
    ]

    for (month, day) in sorted(by_date):
        day_entries = sorted(by_date[(month, day)], key=lambda e: get_field(e, "name"))
        dt_start = datetime.date(BASE_YEAR, month, day)
        dt_end = dt_start + datetime.timedelta(days=1)

        if len(day_entries) == 1:
            e = day_entries[0]
            rel = get_field(e, "relation")
            summary = f"{get_field(e, 'name')} · {rel}" if rel else get_field(e, "name")
        else:
            names = " / ".join(get_field(e, "name") for e in day_entries)
            summary = f"{names}（{len(day_entries)}{unit_label}）"

        desc_parts: list[str] = []
        for e in day_entries:
            eid = get_field(e, "id")
            header_bits = [b for b in (get_field(e, "name"), get_field(e, "subtitle"), get_field(e, "years")) if b]
            block = [" · ".join(header_bits)]
            meta_bits = [b for b in (get_field(e, "field"), get_field(e, "place")) if b]
            if meta_bits:
                block.append("｜".join(meta_bits))
            q = quotes.get(eid)
            q_text = q.get("text", "").strip() if isinstance(q, dict) else (q.strip() if isinstance(q, str) else "")
            if q_text:
                block.append(f"「{q_text}」")
            elif get_field(e, "tagline"):
                block.append(get_field(e, "tagline"))
            card_a = get_field(e, "cardA")
            if card_a:
                label_a = cfg.get("labels", {}).get("cardA", "核心贡献")
                block.append(f"{label_a}：{card_a}")
            desc_parts.append("\n".join(block))

        description = "\n\n".join(desc_parts)

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{slug}-{month:02d}{day:02d}@theme-calendar",
            f"DTSTAMP:{BASE_YEAR}0101T000000Z",
            f"DTSTART;VALUE=DATE:{dt_start.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{dt_end.strftime('%Y%m%d')}",
            "RRULE:FREQ=YEARLY",
            f"SUMMARY:{ics_escape(summary)}",
            f"DESCRIPTION:{ics_escape(description)}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    folded: list[str] = []
    for raw in lines:
        folded.extend(fold_line(raw))
    return "\r\n".join(folded) + "\r\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="生成主题日历 RFC 5545 (.ics) 订阅文件")
    ap.add_argument("--config", required=True, help="主题配置 JSON")
    ap.add_argument("--out", default=None, help="输出 .ics 文件路径")
    ap.add_argument("--check", action="store_true", help="仅校验磁盘文件是否与最新生成一致")
    args = ap.parse_args()

    cfg_path = Path(args.config).resolve()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    entry_path = resolve_cfg_path(cfg_path, cfg["entryFile"])
    cfg_rel = (not Path(cfg["entryFile"]).is_absolute()) and entry_path == (cfg_path.parent / cfg["entryFile"]).resolve()
    entries = json.loads(entry_path.read_text(encoding="utf-8"))
    quotes = json.loads(resolve_cfg_path(cfg_path, cfg["quoteFile"]).read_text(encoding="utf-8")) if cfg.get("quoteFile") else {}

    out_dir = resolve_cfg_path(cfg_path, cfg.get("outputDir", "output/pdf"), prefer_config_dir=cfg_rel)
    slug = slugify(cfg.get("theme", {}).get("nameEn", "theme-calendar"))
    out = Path(args.out) if args.out else (out_dir / f"{slug}.ics")

    content = build_ics(cfg, entries, quotes)
    if args.check:
        if not out.exists() or out.read_bytes() != content.encode("utf-8"):
            print(f"✗ ICS 文件已过期或缺失：{out}", file=sys.stderr)
            return 1
        print(f"✓ ICS 校验通过：{out}")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(content.encode("utf-8"))
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
