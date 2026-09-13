#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""科学家日历数据集体检脚本。

用途：在改动 app/data/scientists.json / app/data/quotes.json / public/avatars.json 之后跑一遍，
把「结构性错误」和「格式不统一」一次性列出来，避免脏数据混入构建产物。

检查项：
  A. 结构：id 唯一、字段齐全、month/day 合法、file 取值在白名单内
  B. 关联：avatars.json 双向一致、quotes.json 不指向未知 id
  C. 文本：中文行文里的半角标点、空白异常、长度越界
  D. 年份：解析 years 字符串，检查生卒先后与合理性

只读脚本，不修改任何文件。
用法：python -X utf8 scripts/audit_data.py
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCIENTISTS = ROOT / "app" / "data" / "scientists.json"
QUOTES = ROOT / "app" / "data" / "quotes.json"
AVATARS = ROOT / "public" / "avatars.json"
AVATAR_DIR = ROOT / "public" / "avatars"

REQUIRED_FIELDS = [
    "id", "month", "day", "name", "latinName", "years",
    "field", "country", "color", "relation", "tagline",
    "story", "contribution", "fact",
]

FIELD_WHITELIST = {"物理", "化学", "生命科学", "数学", "计算机", "天文", "医学", "地球科学"}
COLOR_WHITELIST = {"coral", "blue", "gold", "green", "violet"}

MONTH_LENGTHS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# 半角标点出现在中文字符之间，属于排版错误
HALFWIDTH_COMMA = re.compile(r"[\u4e00-\u9fff],[\u4e00-\u9fff]")
HALFWIDTH_PERIOD = re.compile(r"[\u4e00-\u9fff]\.[\u4e00-\u9fff]")
HALFWIDTH_COLON = re.compile(r"[\u4e00-\u9fff]:[\u4e00-\u9fff]")
HALFWIDTH_SEMI = re.compile(r"[\u4e00-\u9fff];[\u4e00-\u9fff]")
HALFWIDTH_QUESTION = re.compile(r"[\u4e00-\u9fff]\?")
HALFWIDTH_BANG = re.compile(r"[\u4e00-\u9fff]!")
HALFWIDTH_PAREN = re.compile(r"[\u4e00-\u9fff][()][\u4e00-\u9fff]")

TEXT_FIELDS = ["name", "latinName", "years", "country", "relation", "tagline", "story", "contribution", "fact"]

# 句末可接受：句号、叹号、问号、后引号、后括号
SENTENCE_END = ("。", "！", "？", "”", "）", "』", "】")

# 年份写法：-286–211 / 前 287–前 212 / 1640–1718 / 1900–1958 / 1900– / ?–1958
YEAR_RE = re.compile(r"^(-?)(\d{1,4})([–\-~])(-?)(\d{1,4})$")
YEAR_OPEN_RE = re.compile(r"^(-?)(\d{1,4})([–\-~])(\.\.\.|…)?$")


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


# 平年（如 2025）每月天数，二月按 28 天——365 天日历的合法日期全集。
COMMON_YEAR_LENGTHS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def expected_common_year_dates() -> set[tuple[int, int]]:
    """固定平年的 365 个合法 (month, day)，作为覆盖校验的基准集合。"""
    out: set[tuple[int, int]] = set()
    for month in range(1, 13):
        for day in range(1, COMMON_YEAR_LENGTHS[month - 1] + 1):
            out.add((month, day))
    return out


def check_calendar_coverage(scientists: list[dict]) -> list[str]:
    """严格校验：实际覆盖的日期集合必须等于平年 365 天全集。

    注意：本项目支持「同日多人」，因此按「日期集合」校验，不禁止同一天出现多位人物；
    只报告 missing（缺失的平年日期）与 unexpected（平年不应出现、如 2/29）。
    """
    problems: list[str] = []
    expected = expected_common_year_dates()
    actual = {
        (s["month"], s["day"])
        for s in scientists
        if isinstance(s.get("month"), int) and isinstance(s.get("day"), int)
    }
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        shown = "、".join(f"{m}/{d}" for m, d in missing[:20])
        more = "…" if len(missing) > 20 else ""
        problems.append(f"缺失 {len(missing)} 个平年日期（必须恰好覆盖 365 天）：{shown}{more}")
    if unexpected:
        shown = "、".join(f"{m}/{d}" for m, d in unexpected[:20])
        more = "…" if len(unexpected) > 20 else ""
        problems.append(f"存在 {len(unexpected)} 个非法日期（平年不应出现，如 2/29）：{shown}{more}")
    return problems


def audit() -> int:
    scientists = load_json(SCIENTISTS)
    quotes = load_json(QUOTES)
    avatars = load_json(AVATARS)

    problems: list[str] = []
    warnings: list[str] = []

    def bad(msg: str) -> None:
        problems.append(msg)

    def warn(msg: str) -> None:
        warnings.append(msg)

    # ---------- A. 结构 ----------
    seen_ids: dict[str, int] = {}
    seen_names: dict[str, str] = {}
    for index, item in enumerate(scientists):
        label = f"[{index}] {item.get('name', '?')} ({item.get('id', '?')})"

        for key in REQUIRED_FIELDS:
            if key not in item:
                bad(f"{label}: 缺少字段 {key}")

        sid = item.get("id", "")
        if not sid:
            bad(f"{label}: id 为空")
        elif sid in seen_ids:
            bad(f"{label}: id 重复（首次出现于 #{seen_ids[sid]}）")
        else:
            seen_ids[sid] = index

        name = item.get("name", "")
        if name in seen_names:
            warn(f"{label}: 姓名重复（另一条 id={seen_names[name]}）")
        else:
            seen_names[name] = sid

        month, day = item.get("month"), item.get("day")
        if not isinstance(month, int) or not 1 <= month <= 12:
            bad(f"{label}: month 非法 -> {month!r}")
        elif not isinstance(day, int) or not 1 <= day <= MONTH_LENGTHS[month - 1]:
            bad(f"{label}: day 非法 -> {month}月{day}日")
        if month == 2 and day == 29:
            warn(f"{label}: 落在 2 月 29 日，平年无法展示")

        if item.get("field") not in FIELD_WHITELIST:
            bad(f"{label}: field 非法 -> {item.get('field')!r}")
        if item.get("color") not in COLOR_WHITELIST:
            bad(f"{label}: color 非法 -> {item.get('color')!r}")

        # ---------- C. 文本 ----------
        for key in TEXT_FIELDS:
            value = item.get(key)
            if not isinstance(value, str):
                continue
            if value != value.strip():
                bad(f"{label}: {key} 首尾有空白 -> {value!r}")
            if "  " in value:
                warn(f"{label}: {key} 含连续空格")
            for rx, desc in (
                (HALFWIDTH_COMMA, "半角逗号"),
                (HALFWIDTH_PERIOD, "半角句号"),
                (HALFWIDTH_COLON, "半角冒号"),
                (HALFWIDTH_SEMI, "半角分号"),
                (HALFWIDTH_QUESTION, "半角问号"),
                (HALFWIDTH_BANG, "半角叹号"),
                (HALFWIDTH_PAREN, "半角括号"),
            ):
                if rx.search(value):
                    bad(f"{label}: {key} 中文语境出现{desc} -> {value[:60]}")

        story = item.get("story", "")
        if isinstance(story, str) and not story.endswith(SENTENCE_END):
            warn(f"{label}: story 结尾缺少句号 -> …{story[-18:]}")
        if isinstance(story, str) and len(story) < 40:
            warn(f"{label}: story 过短（{len(story)} 字）")

        fact = item.get("fact", "")
        if isinstance(fact, str) and not fact.endswith(SENTENCE_END):
            warn(f"{label}: fact 结尾缺少句号 -> …{fact[-18:]}")

        # ---------- D. 年份 ----------
        years = item.get("years", "")
        if isinstance(years, str):
            parsed = parse_years(years)
            if parsed is None:
                bad(f"{label}: years 无法解析 -> {years!r}")
            else:
                birth, death = parsed
                if birth is not None and death is not None and birth > death:
                    bad(f"{label}: 生年晚于卒年 -> {years!r}")
                if birth is not None and birth < -3000:
                    warn(f"{label}: 生年早于公元前 3000 年 -> {years!r}")
                if death is not None and death > 2026:
                    warn(f"{label}: 卒年在未来 -> {years!r}")
                if birth is not None and birth > 2026:
                    bad(f"{label}: 生年在未来 -> {years!r}")

    # ---------- 365 天覆盖（严格，必须恰好等于平年 365 天）----------
    coverage_problems = check_calendar_coverage(scientists)
    problems.extend(coverage_problems)
    covered = {(s["month"], s["day"]) for s in scientists if isinstance(s.get("month"), int) and isinstance(s.get("day"), int)}
    print(f"人物总数：{len(scientists)}　已覆盖日期：{len(covered)} / 365"
          f"{'　✓ 覆盖完整' if not coverage_problems else '　✗ 覆盖不完整'}")

    # ---------- B. 关联 ----------
    id_set = set(seen_ids)
    for avatar_id, info in avatars.items():
        if avatar_id not in id_set:
            bad(f"avatars.json 指向未知人物：{avatar_id}")
        elif info.get("photo") and not (AVATAR_DIR / f"{avatar_id}.jpg").exists():
            bad(f"avatars.json 标记 {avatar_id} 有照片，但缺少 public/avatars/{avatar_id}.jpg")

    if AVATAR_DIR.exists():
        manifest_ids = set(avatars)
        for file in sorted(AVATAR_DIR.glob("*.jpg")):
            if file.stem not in manifest_ids:
                bad(f"public/avatars/{file.name} 未登记在 avatars.json")
            elif not avatars[file.stem].get("photo"):
                warn(f"public/avatars/{file.name} 存在，但 avatars.json 未标记 photo=true")

    for quote_id, payload in quotes.items():
        if quote_id not in id_set:
            bad(f"quotes.json 指向未知人物：{quote_id}")
        if isinstance(payload, dict):
            if not payload.get("text"):
                bad(f"quotes.json[{quote_id}] 缺少 text")
            if not payload.get("source"):
                bad(f"quotes.json[{quote_id}] 缺少 source")
            if isinstance(payload.get("text"), str) and not payload["text"].endswith(SENTENCE_END):
                warn(f"quotes.json[{quote_id}] text 结尾缺少标点 -> …{payload['text'][-18:]}")

    quote_coverage = len(set(quotes) & id_set)
    print(f"语录覆盖：{quote_coverage} / {len(scientists)}　头像登记：{len(avatars)}　照片：{sum(1 for v in avatars.values() if v.get('photo'))}")

    # ---------- 输出 ----------
    print()
    if warnings:
        print(f"⚠ 提醒 {len(warnings)} 条：")
        for line in warnings:
            print("  -", line)
        print()
    if problems:
        print(f"✗ 错误 {len(problems)} 条：")
        for line in problems:
            print("  -", line)
        return 1
    print("✓ 未发现结构性错误")
    return 0


def parse_years(raw: str):
    """'1640–1718' -> (1640, 1718)；'-286–211' -> (-286, 211)；'1900–' -> (1900, None)。"""
    text = unicodedata.normalize("NFKC", raw).strip().replace(" ", "")
    text = text.replace("前", "-").replace("BC", "-").replace("BCE", "-")
    text = text.replace("∼", "~").replace("～", "~").replace("—", "–")

    match = YEAR_RE.match(text)
    if match:
        b_neg, b, _, d_neg, d = match.groups()
        return (int(b) * (-1 if b_neg else 1), int(d) * (-1 if d_neg else 1))
    match = YEAR_OPEN_RE.match(text)
    if match:
        b_neg, b, _, _ = match.groups()
        return (int(b) * (-1 if b_neg else 1), None)
    if re.match(r"^c?\.?\s*(-?\d{1,4})$", text):
        return (int(text.replace("c", "").replace(".", "")), None)
    return None


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(audit())
