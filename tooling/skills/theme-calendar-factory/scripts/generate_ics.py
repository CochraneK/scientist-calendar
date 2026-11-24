#!/usr/bin/env python3
"""主题日历通用 RFC 5545 订阅日历 (.ics) 生成器。

用法：
  python generate_ics.py --config theme.json [--out output/theme.ics] [--check]

特点：
  - 完全由 theme.json 驱动，换主题不改代码；
  - 同一日期有多位人物时自动合并为单条全天年度循环事件（RRULE:FREQ=YEARLY）；
  - 可选配置 ics.requireFullYear（强制校验 365 天全覆盖）、ics.includeLinks + site.*（附带人物永久链接与 CATEGORIES）；
  - 严格遵守 RFC 5545 §3.1：UTF-8 75 字节折行 + CRLF 行尾，兼容 Apple / Google / Outlook / 飞书日历。
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import urllib.parse
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
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def fold_line(line: str, max_octets: int = 75) -> list[str]:
    """RFC 5545 §3.1: 按 UTF-8 字节数折行，绝不切断多字节中文字符。"""
    if len(line.encode("utf-8")) <= max_octets:
        return [line]
    out: list[str] = []
    cur = ""
    for ch in line:
        cand = cur + ch
        if cur and len(cand.encode("utf-8")) > max_octets:
            out.append(cur)
            cur = " " + ch
        else:
            cur = cand
    if cur:
        out.append(cur)
    return out


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "theme-calendar"


def entry_url(cfg: dict, entry_id: str) -> str:
    site = cfg.get("site", {})
    origin = str(site.get("origin", "")).rstrip("/")
    base = str(site.get("basePath", "")).rstrip("/")
    segment = str(site.get("entryRouteSegment", "entries")).strip("/")
    if not origin:
        return ""
    return f"{origin}{base}/{segment}/{urllib.parse.quote(entry_id, safe='')}/"


def build_ics(cfg: dict, entries: list[dict], quotes: dict) -> str:
    theme = cfg.get("theme", {})
    ics_cfg = cfg.get("ics", {})
    fm = cfg["fieldMap"]
    theme_name = theme.get("name", "主题日历")
    theme_en = theme.get("nameEn", "Theme Calendar")
    unit_label = theme.get("unitLabel", "位人物")
    slug = slugify(ics_cfg.get("uidPrefix") or theme_en)
    uid_domain = ics_cfg.get("uidDomain", "theme-calendar")
    prod_id = ics_cfg.get("prodId", f"-//{theme_en}//Theme Calendar Factory//ZH")
    cal_name = ics_cfg.get("calName", theme_name)
    cal_desc = ics_cfg.get("calDesc", f"{theme_name}：每天认识一{unit_label}")
    summary_prefix = str(ics_cfg.get("summaryPrefix", "")).strip()
    require_full_year = bool(ics_cfg.get("requireFullYear", False))
    include_links = bool(ics_cfg.get("includeLinks", False))
    label_a = cfg.get("labels", {}).get("cardA", "核心贡献")

    def get_field(entry: dict, role: str) -> str:
        key = fm.get(role)
        return str(entry.get(key, "") or "").strip() if key else ""

    by_date: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for entry in entries:
        by_date[(int(entry[fm["month"]]), int(entry[fm["day"]]))].append(entry)

    if require_full_year:
        date_sequence: list[tuple[int, int]] = []
        cursor = datetime.date(BASE_YEAR, 1, 1)
        end = datetime.date(BASE_YEAR, 12, 31)
        while cursor <= end:
            key = (cursor.month, cursor.day)
            if key not in by_date:
                raise RuntimeError(f"缺少 {cursor.month}/{cursor.day} 的条目，无法生成完整 365 天日历")
            date_sequence.append(key)
            cursor += datetime.timedelta(days=1)
    else:
        date_sequence = sorted(by_date)

    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{prod_id}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{ics_escape(cal_name)}",
        f"X-WR-CALDESC:{ics_escape(cal_desc)}",
    ]

    for (month, day) in date_sequence:
        day_entries = by_date[(month, day)] if require_full_year else sorted(
            by_date[(month, day)], key=lambda e: get_field(e, "name")
        )
        dt_start = datetime.date(BASE_YEAR, month, day)
        dt_end = dt_start + datetime.timedelta(days=1)
        primary = day_entries[0]

        if summary_prefix:
            if len(day_entries) == 1:
                field_txt = get_field(primary, "field")
                summary = f"{summary_prefix}：{get_field(primary, 'name')}" + (f"（{field_txt}）" if field_txt else "")
            else:
                summary = f"{summary_prefix}：{get_field(primary, 'name')} 等 {len(day_entries)} 位"
        elif len(day_entries) == 1:
            rel = get_field(primary, "relation")
            summary = f"{get_field(primary, 'name')} · {rel}" if rel else get_field(primary, "name")
        else:
            names = " / ".join(get_field(e, "name") for e in day_entries)
            summary = f"{names}（{len(day_entries)}{unit_label}）"

        desc_parts: list[str] = []
        for idx, e in enumerate(day_entries, start=1):
            eid = get_field(e, "id")
            prefix = f"[{idx}/{len(day_entries)}] " if len(day_entries) > 1 and include_links else ""
            sub_bits = [b for b in (get_field(e, "subtitle"), get_field(e, "years")) if b]
            head = f"{prefix}{get_field(e, 'name')}" + (f"（{' · '.join(sub_bits)}）" if sub_bits else "")
            block = [head]
            meta_bits = [b for b in (get_field(e, "place"), get_field(e, "field"), get_field(e, "relation")) if b]
            if meta_bits:
                block.append(" · ".join(meta_bits))
            tagline = get_field(e, "tagline")
            if tagline:
                block.append(f"阅读线索：{tagline}")
            card_a = get_field(e, "cardA")
            if card_a:
                block.append(f"{label_a}：{card_a}")
            q = quotes.get(eid)
            q_text = q.get("text", "").strip() if isinstance(q, dict) else (q.strip() if isinstance(q, str) else "")
            q_src = q.get("source", "").strip() if isinstance(q, dict) else ""
            if q_text:
                block.append(f"引语：“{q_text}”" + (f" — {q_src}" if q_src else ""))
            if include_links:
                link = entry_url(cfg, eid)
                if link:
                    block.append(f"人物档案：{link}")
            desc_parts.append("\n".join(block))

        description = "\n\n".join(desc_parts)
        vevent = [
            "BEGIN:VEVENT",
            f"UID:{slug}-{month:02d}{day:02d}@{uid_domain}",
            f"DTSTAMP:{BASE_YEAR}0101T000000Z",
            f"DTSTART;VALUE=DATE:{dt_start.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{dt_end.strftime('%Y%m%d')}",
            "RRULE:FREQ=YEARLY",
            f"SUMMARY:{ics_escape(summary)}",
            f"DESCRIPTION:{ics_escape(description)}",
        ]
        if include_links:
            primary_link = entry_url(cfg, get_field(primary, "id"))
            if primary_link:
                vevent.append(f"URL:{primary_link}")
        categories = list(dict.fromkeys([theme_name, *(get_field(e, "field") for e in day_entries if get_field(e, "field"))]))
        if categories:
            vevent.append(f"CATEGORIES:{ics_escape(','.join(categories))}")
        vevent.extend([
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ])
        lines.extend(vevent)

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

    ics_cfg = cfg.get("ics", {})
    if args.out:
        out = Path(args.out)
    elif ics_cfg.get("outputPath"):
        out = resolve_cfg_path(cfg_path, ics_cfg["outputPath"], prefer_config_dir=cfg_rel)
    else:
        out_dir = resolve_cfg_path(cfg_path, cfg.get("outputDir", "output/pdf"), prefer_config_dir=cfg_rel)
        slug = slugify(cfg.get("theme", {}).get("nameEn", "theme-calendar"))
        out = out_dir / f"{slug}.ics"

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
