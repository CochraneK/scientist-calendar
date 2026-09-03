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
    """把儒略历日期换算为格里历（proleptic，适用于 1582 年前后的全部年份）。

    坑（原先这里是静默失效的恒等变换）：
      不能用 datetime.date(y, m, d).toordinal() 求儒略日 —— datetime 用的是
      「前置格里历」(proleptic Gregorian)，会把输入的儒略历日期当成格里历，
      于是变成「格里历 -> JDN -> 格里历」的恒等运算，换算永远不生效，
      导致一批 9~13 天偏移的历史人物被误报为日期错误。
      儒略历日期必须先用儒略历专用公式算 JDN，再用 Fliegel–Van Flandern
      逆变换转回格里历。
    """
    # 1) 儒略历日期 -> 儒略日 JDN（儒略历专用公式）
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jd = day + (153 * m + 2) // 5 + 365 * y + y // 4 - 32083
    # 2) 儒略日 -> 格里历（Fliegel–Van Flandern 逆变换，格里历版）
    b = jd + 32044
    c = (4 * b + 3) // 146097
    d = b - (146097 * c) // 4
    e = (4 * d + 3) // 1461
    f = d - (1461 * e) // 4
    g = (5 * f + 2) // 153
    day_out = f - (153 * g + 2) // 5 + 1
    month_out = g + 3 - 12 * (g // 10)
    year_out = 100 * c + e - 4800 + g // 10
    return year_out, month_out, day_out


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
    calendar_issues: list[str] = []
    qid_issues: list[str] = []
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

        # ---- 先算好年份与 QID 可信度，日期比对要用 ----
        birth_years = {year for _, year, _, _, _ in births}
        death_years = {year for _, year, _, _, _ in deaths}
        dataset_years = parse_dataset_years(entry.get("years", ""))
        d_birth = int(dataset_years[0]) if dataset_years and dataset_years[0] else None
        d_death = (
            int(dataset_years[1])
            if dataset_years and len(dataset_years) > 1 and dataset_years[1]
            else None
        )
        # QID 存疑：生/卒年相差 >2 年，几乎不可能是同一人（多半挂到同名或他人条目）。
        # 一旦 QID 存疑，日期比对就是在跟"另一个人"比，结果无意义 → 并入 QID 清单。
        qid_suspect = bool(
            (d_birth is not None and birth_years and all(abs(y - d_birth) > 2 for y in birth_years))
            or (d_death is not None and death_years and all(abs(y - d_death) > 2 for y in death_years))
        )

        # 1) 日期：任一非 deprecated 声明与档案一致即通过。
        #    重要：Wikidata 很多条目把"旧历(儒略历)日期"直接存为格里历串而不带历法限定符，
        #    因此除直接比对，还要比对"该日期按儒略→格里换算后"是否等于档案日期。
        raw_candidates = {
            (month, day)
            for _, year, month, day, _ in births
            if month and day
        }
        candidates = set(raw_candidates)
        calendar_notes = []
        calendar_hit = False
        for _, year, month, day, _ in births:
            if not (month and day):
                continue
            try:
                gy, gm, gd = julian_to_gregorian(year, month, day)
            except ValueError:
                continue
            if (gm, gd) not in candidates:
                candidates.add((gm, gd))
            if (gm, gd) == (dataset_month, dataset_day) and (month, day) not in raw_candidates:
                calendar_hit = True
                calendar_notes.append(
                    f"{label}: 档案 {dataset_month}月{dataset_day}日(格里) = Wikidata "
                    f"{month}月{day}日(儒略) —— 历法差异非错误"
                )
        # 2) 反向：档案存的是旧历(儒略历)，Wikidata 存的是换算后的格里历。
        #    例：开普勒 档案 1571年12月27日(儒略) = 1572年1月6日(格里)，
        #    连"生年 1571 vs 1572"的差异也是历法造成的，所以命中后要豁免年份比对。
        if not calendar_hit and d_birth is not None:
            try:
                fy, fm, fd = julian_to_gregorian(d_birth, dataset_month, dataset_day)
            except ValueError:
                fy = fm = fd = None
            if fm and (fm, fd) in raw_candidates:
                calendar_hit = True
                calendar_issues.append(
                    f"{label}: 档案 {d_birth}年{dataset_month}月{dataset_day}日(儒略) = "
                    f"{fy}年{fm}月{fd}日(格里)，Wikidata 采用格里历 —— 历法差异非错误"
                )
        if candidates and (dataset_month, dataset_day) not in candidates and not calendar_hit:
            shown = "、".join(f"{m}月{d}日" for m, d in sorted(raw_candidates))
            msg = f"{label}: 档案 {dataset_month}月{dataset_day}日，Wikidata 记录 {shown}"
            if qid_suspect:
                # 跟"另一个人"比日期没有意义，并入 QID 清单
                qid_issues.append(msg + " —— 随 QID 存疑，需先核对 QID")
            else:
                date_issues.append(msg)
        # 命中「换算后一致」的，归入历法差异清单（信息，不算错误）
        calendar_issues.extend(calendar_notes)

        # 3) 年份：历法差异造成的跨年（如开普勒 1571→1572）不视为错误
        if not calendar_hit and dataset_years:
            d_birth, d_death = dataset_years
            # 年份相差 >2 年几乎不可能是同一人 —— 多半是 QID 挂到了同名/他人条目，
            if birth_years and d_birth not in birth_years:
                if all(abs(y - d_birth) > 2 for y in birth_years):
                    qid_issues.append(
                        f"{label}: 档案生年 {d_birth}，Wikidata "
                        f"{'、'.join(map(str, sorted(birth_years)))} —— QID 可能指向他人，请核对"
                    )
                else:
                    year_issues.append(
                        f"{label}: 档案生年 {d_birth}，Wikidata {'、'.join(map(str, sorted(birth_years)))}"
                    )
            if d_death is not None and death_years and d_death not in death_years:
                if all(abs(y - d_death) > 2 for y in death_years):
                    qid_issues.append(
                        f"{label}: 档案卒年 {d_death}，Wikidata "
                        f"{'、'.join(map(str, sorted(death_years)))} —— QID 可能指向他人，请核对"
                    )
                else:
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
    print()
    # 以下两类均为"信息"，不算数据错误：历法差异是 Wikidata 存旧历所致，
    # QID 存疑是校验锚点挂错人所致，都需要改脚本/改 QID，而不是改数据。
    if calendar_issues:
        print(f"ℹ 历法差异（儒略历→格里历，档案正确，非错误）{len(calendar_issues)} 条：")
        for line in calendar_issues:
            print("  -", line)
        print()
    if qid_issues:
        print(f"⚠ QID 疑似指向他人（需核对 QID，不建议盲改数据）{len(qid_issues)} 条：")
        for line in qid_issues:
            print("  -", line)
        print()
    real_errors = len(date_issues) + len(year_issues)
    print(f"== 汇总：真实数据错误 {real_errors} 条；"
          f"历法差异 {len(calendar_issues)} 条；QID 存疑 {len(qid_issues)} 条 ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
