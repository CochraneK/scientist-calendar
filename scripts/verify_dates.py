#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 Wikidata 交叉核验科学家日历的生卒日期。

数据源说明：`app/scientists.json` 里 `auto-q<QID>` 形式的 id 直接对应 Wikidata 实体号；
其余自定义 id（如 newton、einstein）用拉丁姓名回查 Wikidata 搜索接口定位实体。

核验要点：
  1. 只采纳 rank=preferred 的日期声明，其次 normal，跳过 deprecated；
  2. 区分历法：Wikidata 常同时存儒略历（Q1985786）与格里历（Q1985727）两套日期，
     本脚本把儒略历日期换算成格里历再比对（数据集统一使用格里历）；
  3. 只要任一非 deprecated 声明与档案一致，就算通过 —— 避免同源异值造成的误报。

已知误报（本脚本按姓名回查，撞到同名人物会报不一致，实际数据集是正确的）：
  - nash / hamilton / kamen / backus / friedmann / hardy-weinberg：
    搜索命中了同名的建筑师、演员等，数据集值经人工核对无误。
  - 盖伦：Wikidata 的 P570 存在"300"（世纪精度）的冗余声明，数据集 216 为学界共识。
  - 焦耳 / 陈省身：Wikidata 存在少数来源的异值声明，数据集值为通行说法。

只读脚本，不修改任何文件。
用法：python -X utf8 scripts/verify_dates.py [--limit N]
"""

from __future__ import annotations

import datetime
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "app" / "scientists.json"
CACHE = ROOT / "output" / "wikidata-cache.json"   # output/ 已被 .gitignore 忽略
API = "https://www.wikidata.org/w/api.php"
HEADERS = {"User-Agent": "scientist-calendar/1.0 (data verification script)"}
BATCH = 45

QID_JULIAN = "Q1985786"
QID_GREGORIAN = "Q1985727"
RANK_ORDER = {"preferred": 0, "normal": 1, "deprecated": 2}


def api_get(params: dict) -> dict:
    url = f"{API}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            if attempt == 2:
                print(f"  ! 请求失败：{exc}", file=sys.stderr)
                return {}
            time.sleep(2 + attempt * 3)
    return {}


def julian_to_gregorian(year: int, month: int, day: int):
    """把儒略历日期换算为格里历（proleptic，适用于 1582 年前后的全部年份）。"""
    jd = datetime.date(year, month, day).toordinal() + 1_721_425
    # 儒略日 -> 格里历（算法参考 Fliegel–Van Flandern 逆变换）
    alpha = int((jd - 1_867_216.25) / 36524.25)
    a = jd + 1 + alpha - (alpha // 4)
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day = int(b - d - int(30.6001 * e))
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    return year, month, day


def parse_claim(value: dict):
    """返回 (year, month, day, calendar_qid)；精度不足时月/日为 None。"""
    raw = value.get("time")
    if not raw:
        return None
    calendar = (value.get("calendarmodel") or "").rsplit("/", 1)[-1]
    match = re.match(r"^([+-])(\d{1,16})-(\d{2})-(\d{2})T", raw)
    if match:
        sign, year, month, day = match.groups()
        month, day = int(month), int(day)
        if month == 0 or day == 0:                      # 只精确到年月/年
            return (int(year) * (-1 if sign == "-" else 1), None, None, calendar)
        return (int(year) * (-1 if sign == "-" else 1), month, day, calendar)
    match = re.match(r"^([+-])(\d{1,16})", raw)
    if match:
        sign, year = match.groups()
        return (int(year) * (-1 if sign == "-" else 1), None, None, calendar)
    return None


def entity_dates(entity: dict, prop: str) -> list[tuple]:
    """返回该属性下所有非 deprecated 的日期，按 rank 排序，已统一换算为格里历。"""
    out = []
    for claim in entity.get("claims", {}).get(prop, []):
        if claim.get("rank") == "deprecated":
            continue
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        parsed = parse_claim(value)
        if not parsed:
            continue
        year, month, day, calendar = parsed
        if calendar == QID_JULIAN and month and day:
            try:
                year, month, day = julian_to_gregorian(year, month, day)
            except ValueError:
                pass
        out.append((RANK_ORDER.get(claim.get("rank"), 1), year, month or 0, day or 0, calendar))
    # 用 -1 占位 None，避免排序时 None 与 int 比较报错
    return sorted(out, key=lambda row: (row[0], row[1], row[2], row[3]))


def parse_dataset_years(raw: str):
    text = (raw or "").replace(" ", "")
    text = text.replace("约", "").replace("前", "-").replace("至今", "")
    match = re.match(r"^(-?\d{1,4})[–\-~](-?\d{1,4})?$", text)
    if not match:
        return None
    birth, death = match.groups()
    return (int(birth), int(death) if death else None)


def search_qid(name: str) -> str | None:
    payload = api_get({
        "action": "wbsearchentities",
        "search": name,
        "language": "en",
        "limit": 1,
        "type": "item",
        "format": "json",
    })
    results = payload.get("search") or []
    return results[0]["id"] if results else None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    scientists = json.loads(DATA.read_text(encoding="utf-8"))
    if "--limit" in sys.argv:
        scientists = scientists[: int(sys.argv[sys.argv.index("--limit") + 1])]

    # 1) 建立 id -> QID 映射
    qids: dict[str, str] = {}
    need_search: list[dict] = []
    for entry in scientists:
        match = re.fullmatch(r"auto-q(\d+)", entry.get("id", ""))
        if match:
            qids[entry["id"]] = f"Q{match.group(1)}"
        else:
            need_search.append(entry)

    print(f"档案 {len(scientists)} 条：直接命中 QID {len(qids)} 条，需按姓名回查 {len(need_search)} 条")

    # Wikidata 对匿名请求限流较严（429），把实体与搜索结果缓存起来，便于反复重跑。
    cache: dict = {"search": {}, "entities": {}}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
        cache.setdefault("search", {})
        cache.setdefault("entities", {})

    for index, entry in enumerate(need_search, 1):
        name = entry.get("latinName") or entry.get("name", "")
        if name in cache["search"]:
            found = cache["search"][name]
        else:
            found = search_qid(name)
            cache["search"][name] = found
            time.sleep(0.6)                       # 搜索接口限流更严，放慢一点
        if found:
            qids[entry["id"]] = found
        if index % 40 == 0:
            print(f"  已回查 {index}/{len(need_search)}")
    print(f"  可核验实体共 {len(qids)} 条")

    # 2) 批量抓取实体（命中的走缓存）
    entities: dict[str, dict] = {}
    missing: list[str] = []
    for qid in qids.values():
        if qid in cache["entities"]:
            entities[qid] = cache["entities"][qid]
        else:
            missing.append(qid)
    if entities:
        print(f"  缓存命中 {len(entities)} 条，需抓取 {len(missing)} 条")

    fetched = 0
    for index in range(0, len(missing), BATCH):
        chunk = missing[index:index + BATCH]
        payload = api_get({
            "action": "wbgetentities",
            "ids": "|".join(chunk),
            "props": "claims|labels",
            "languages": "zh|en",
            "format": "json",
        })
        for qid, entity in (payload.get("entities") or {}).items():
            if "missing" not in entity:
                entities[qid] = entity
                cache["entities"][qid] = entity
        fetched += len(chunk)
        print(f"  已抓取 {fetched}/{len(missing)}")
        time.sleep(1.0)

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    # 只保留核验需要的字段，避免完整实体声明把缓存撑到几十 MB。
    slim = {
        qid: {"claims": {p: entity.get("claims", {}).get(p, []) for p in ("P569", "P570")}}
        for qid, entity in cache["entities"].items()
    }
    CACHE.write_text(json.dumps({"search": cache["search"], "entities": slim}, ensure_ascii=False), encoding="utf-8")
    print(f"  已写入缓存 {CACHE.relative_to(ROOT)}（仅保留 P569/P570）")

    date_issues: list[str] = []
    year_issues: list[str] = []
    no_data: list[str] = []

    for entry in scientists:
        qid = qids.get(entry["id"])
        entity = entities.get(qid) if qid else None
        if not entity:
            no_data.append(entry["id"])
            continue

        births = entity_dates(entity, "P569")
        deaths = entity_dates(entity, "P570")
        if not births:
            no_data.append(entry["id"])
            continue

        label = f"{entry['name']}（{entry['id']} / {qid}）"
        dataset_month, dataset_day = entry["month"], entry["day"]

        # 1) 日期：只要任一非 deprecated 声明与档案一致即通过
        candidates = {
            (month, day)
            for _, year, month, day, _ in births
            if month and day
        }
        if candidates and (dataset_month, dataset_day) not in candidates:
            shown = "、".join(f"{m}月{d}日" for m, d in sorted(candidates))
            date_issues.append(f"{label}: 档案 {dataset_month}月{dataset_day}日，Wikidata 记录 {shown}")

        # 2) 年份
        birth_years = {year for _, year, _, _, _ in births}
        death_years = {year for _, year, _, _, _ in deaths}
        dataset_years = parse_dataset_years(entry.get("years", ""))
        if dataset_years:
            d_birth, d_death = dataset_years
            if birth_years and d_birth not in birth_years:
                year_issues.append(
                    f"{label}: 档案生年 {d_birth}，Wikidata {'、'.join(map(str, sorted(birth_years)))}"
                )
            if d_death is not None and death_years and d_death not in death_years:
                year_issues.append(
                    f"{label}: 档案卒年 {d_death}，Wikidata {'、'.join(map(str, sorted(death_years)))}"
                )

    print()
    if no_data:
        print(f"（{len(no_data)} 条在 Wikidata 未找到可比对日期，已跳过：{'、'.join(no_data[:20])}"
              f"{'…' if len(no_data) > 20 else ''}）\n")
    if date_issues:
        print(f"✗ 出生日期不一致 {len(date_issues)} 条：")
        for line in date_issues:
            print("  -", line)
    else:
        print("✓ 出生日期全部与 Wikidata 一致")
    print()
    if year_issues:
        print(f"✗ 生卒年份不一致 {len(year_issues)} 条：")
        for line in year_issues:
            print("  -", line)
    else:
        print("✓ 生卒年份全部与 Wikidata 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
