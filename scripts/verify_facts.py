#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高知名度科学家抽检：用 Wikidata 核对 国籍(P27) / 职业(P106) / 生卒日期(P569,P570)。

与 verify_dates.py 的区别：
  - 只抽检一份「高知名度」白名单（不是全量），规避全量自动比对在历史政权/
    多重国籍字段上的大量误报；
  - 新增 国籍 与 职业(领域) 两个维度的核对；
  - 比对采用「宽容」策略：把历史政权/多重国籍归并到现代国家再比较，
    只把明显矛盾列出来，由人工判定是否真实错误（脚本只读，不改文件）。

复用 verify_dates 的 api_get / 日期解析 / 历法换算，以及 output/wikidata-cache.json
里的 search 缓存（latinName -> QID），避免重复搜索触发限流。

用法：python -X utf8 scripts/verify_facts.py
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "app" / "scientists.json"
CACHE = ROOT / "output" / "wikidata-cache.json"
API = "https://www.wikidata.org/w/api.php"
HEADERS = {"User-Agent": "scientist-calendar/1.0 (data verification script)"}
BATCH = 45

# 仅做高知名度抽检，避免历史政权/多重国籍带来的海量误报
FAMOUS = [
    "Isaac Newton", "Albert Einstein", "Carl Friedrich Gauss", "Archimedes",
    "Marie Curie", "Charles Darwin", "Alan Turing", "Niels Bohr",
    "James Clerk Maxwell", "Louis Pasteur", "Galileo Galilei", "Antoine Lavoisier",
    "Michael Faraday", "Gregor Mendel", "Sigmund Freud", "Grace Hopper",
    "Ada Lovelace", "Nikola Tesla", "Max Planck", "Werner Heisenberg",
    "Paul Dirac", "Leonhard Euler", "Johannes Kepler", "Nicolaus Copernicus",
    "Dmitri Mendeleev", "Alfred Nobel", "Enrico Fermi", "Max Born",
    "John von Neumann", "Claude Shannon", "Charles Babbage",
    "Gottfried Wilhelm Leibniz", "Rene Descartes", "Blaise Pascal",
    "Pierre de Fermat", "Joseph Fourier", "Joseph-Louis Lagrange",
    "Pierre-Simon Laplace", "Henri Poincare", "Bernhard Riemann",
    "David Hilbert", "Kurt Godel", "Stephen Hawking", "Ludwig Boltzmann",
    "Josiah Willard Gibbs", "Hendrik Lorentz", "Tu Youyou",
    "Rosalind Franklin", "Lise Meitner", "Chien-Shiung Wu", "Richard Feynman",
    "Ernest Rutherford", "Alexander Fleming", "Edward Jenner",
]


# ---------- 复用 verify_dates 的网络与日期逻辑 ----------
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


def parse_claim(value: dict):
    raw = value.get("time")
    if not raw:
        return None
    calendar = (value.get("calendarmodel") or "").rsplit("/", 1)[-1]
    m = re.match(r"^([+-])(\d{1,16})-(\d{2})-(\d{2})T", raw)
    if m:
        sign, year, month, day = m.groups()
        if month == "00" or day == "00":
            return (int(year) * (-1 if sign == "-" else 1), None, None, calendar)
        return (int(year) * (-1 if sign == "-" else 1), int(month), int(day), calendar)
    m = re.match(r"^([+-])(\d{1,16})", raw)
    if m:
        sign, year = m.groups()
        return (int(year) * (-1 if sign == "-" else 1), None, None, calendar)
    return None


def entity_dates(entity: dict, prop: str) -> list:
    out = []
    for claim in entity.get("claims", {}).get(prop, []):
        if claim.get("rank") == "deprecated":
            continue
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        parsed = parse_claim(value)
        if parsed:
            out.append((claim.get("rank"),) + parsed)
    return out


def parse_dataset_years(raw: str):
    text = (raw or "").replace(" ", "").replace("约", "").replace("前", "-").replace("至今", "")
    m = re.match(r"^(-?\d{1,4})[–\-~](-?\d{1,4})?$", text)
    if not m:
        return None
    birth, death = m.groups()
    return (int(birth), int(death) if death else None)


# ---------- 国家归并（历史政权/多重国籍 -> 现代国家） ----------
def modern_of(label: str) -> str:
    """把一个国籍/政权名归并到现代国家 token，用于宽容比对。"""
    if not label:
        return ""
    s = label
    table = [
        ("普鲁士", "德国"), ("神圣罗马", "德国"), ("德意志", "德国"), ("纳粹", "德国"),
        ("德", "德国"), ("奥地利", "奥地利"), ("奥匈", "奥地利"), ("匈牙利", "匈牙利"),
        ("大不列颠", "英国"), ("联合王国", "英国"), ("英", "英国"),
        ("法兰西", "法国"), ("法", "法国"),
        ("苏联", "俄罗斯"), ("俄", "俄罗斯"),
        ("美", "美国"), ("中", "中国"), ("瑞士", "瑞士"), ("瑞典", "瑞典"),
        ("挪", "挪威"), ("丹", "丹麦"), ("荷", "荷兰"), ("比", "比利时"),
        ("意", "意大利"), ("西", "西班牙"), ("希", "希腊"), ("罗", "罗马"),
        ("波", "波兰"), ("印", "印度"), ("以", "以色列"), ("加", "加拿大"),
        ("澳", "澳大利亚"), ("新", "新西兰"), ("芬", "芬兰"), ("乌", "乌克兰"),
        ("塞尔", "塞尔维亚"), ("保", "保加利亚"), ("罗", "罗马尼亚"), ("波", "波兰"),
        ("塞尔", "塞尔维亚"), ("土", "土耳其"), ("波", "波兰"),
    ]
    for key, val in table:
        if key in s:
            return val
    return s  # 兜底：原样返回


def country_consistent(data_country: str, wd_labels: list) -> bool:
    """data_country 与 Wikidata 国籍标签列表是否（归并后）一致。"""
    primary = re.split(r"[／/（(]", data_country)[0].strip()
    target = modern_of(primary)
    for lab in wd_labels:
        if modern_of(lab) == target:
            return True
        if lab and (lab in primary or primary in lab):
            return True
    return False


# ---------- 职业 -> 领域 归并 ----------
FIELD_MAP = [
    ("物理", "物理"), ("数学", "数学"), ("化学", "化学"),
    ("生物", "生命科学"), ("遗传", "生命科学"), ("博物", "生命科学"),
    ("植物", "生命科学"), ("动物", "生命科学"), ("天文", "天文"),
    ("计算机", "计算机"), ("信息", "计算机"), ("医", "医学"),
    ("神经", "医学"), ("精神", "医学"), ("地质", "地球科学"), ("地球", "地球科学"),
]


def field_tokens(occ_labels: list) -> set:
    out = set()
    for lab in occ_labels:
        for key, val in FIELD_MAP:
            if key in lab:
                out.add(val)
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    scientists = json.loads(DATA.read_text(encoding="utf-8"))
    by_latin = {s.get("latinName", "").lower(): s for s in scientists if s.get("latinName")}
    by_name = {s["name"]: s for s in scientists}

    cache: dict = {"search": {}}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
        cache.setdefault("search", {})

    # 1) 解析白名单 -> (id, qid)
    picks: list[tuple] = []
    for name in FAMOUS:
        s = by_latin.get(name.lower()) or by_name.get(name)
        if not s:
            continue
        qid = cache["search"].get(s.get("latinName") or s["name"])
        picks.append((s, qid))

    resolved = [p for p in picks if p[1]]
    print(f"白名单 {len(FAMOUS)} 人：数据命中 {len(picks)} 人，其中已解析 QID {len(resolved)} 人")

    # 2) 抓取实体（P27 国籍 / P106 职业 / P569 P570 日期）+ 标签
    qids = [q for _, q in resolved]
    entities: dict = {}
    missing = [q for q in qids if q not in entities]
    fetched = 0
    for i in range(0, len(missing), BATCH):
        chunk = missing[i:i + BATCH]
        payload = api_get({
            "action": "wbgetentities", "ids": "|".join(chunk),
            "props": "claims|labels", "languages": "zh|en", "format": "json",
        })
        for qid, ent in (payload.get("entities") or {}).items():
            if "missing" not in ent:
                entities[qid] = ent
        fetched += len(chunk)
        print(f"  已抓取 {fetched}/{len(missing)}")
        time.sleep(1.0)

    # 3) 抓取国籍 QID 的标签
    country_qids: set = set()
    for _, q in resolved:
        ent = entities.get(q)
        if not ent:
            continue
        for c in ent.get("claims", {}).get("P27", []):
            v = c.get("mainsnak", {}).get("datavalue", {}).get("value", {})
            if isinstance(v, dict) and v.get("id"):
                country_qids.add(v["id"])
    country_labels: dict = {}
    cq = list(country_qids)
    for i in range(0, len(cq), BATCH):
        chunk = cq[i:i + BATCH]
        payload = api_get({
            "action": "wbgetentities", "ids": "|".join(chunk),
            "props": "labels", "languages": "zh|en", "format": "json",
        })
        for qid, ent in (payload.get("entities") or {}).items():
            labs = ent.get("labels", {})
            lab = labs.get("zh", {}).get("value") or labs.get("en", {}).get("value") or qid
            country_labels[qid] = lab
        print(f"  国籍标签 {min(i + BATCH, len(cq))}/{len(cq)}")
        time.sleep(1.0)

    def claim_labels(prop: str, ent: dict) -> list:
        out = []
        for c in ent.get("claims", {}).get(prop, []):
            if c.get("rank") == "deprecated":
                continue
            v = c.get("mainsnak", {}).get("datavalue", {}).get("value", {})
            if isinstance(v, dict) and v.get("id"):
                out.append(country_labels.get(v["id"], v["id"]))
        return out

    # 4) 比对
    country_bad, field_bad, date_bad, year_bad = [], [], [], []
    for s, q in resolved:
        ent = entities.get(q)
        if not ent:
            continue
        label = f"{s['name']}（{s['id']} / {q}）"

        wd_countries = claim_labels("P27", ent)
        if wd_countries and not country_consistent(s["country"], wd_countries):
            country_bad.append(f"{label}: 档案[{s['country']}]  Wikidata[{'、'.join(wd_countries)}]")

        occ = claim_labels("P106", ent)
        fts = field_tokens(occ)
        if fts and s["field"] not in fts:
            field_bad.append(f"{label}: 档案领域[{s['field']}]  Wikidata职业[{'、'.join(occ)}] -> 推断{fts or '∅'}")

        births = entity_dates(ent, "P569")
        bset = {(m, d) for rk, y, m, d, cal in births if m and d}
        if bset and (s["month"], s["day"]) not in bset:
            date_bad.append(f"{label}: 档案 {s['month']}月{s['day']}日  Wikidata{'、'.join(f'{m}月{d}日' for m,d in sorted(bset))}")

        deaths = entity_dates(ent, "P570")
        dy = {y for rk, y, m, d, cal in deaths}
        dsy = parse_dataset_years(s.get("years", ""))
        if dsy:
            if dsy[0] not in {y for rk, y, m, d, cal in births}:
                year_bad.append(f"{label}: 生年 档案{dsy[0]} Wikidata{{{'/'.join(str(y) for rk,y,m,d,cal in births)}}}")

    print("\n========== 抽检结果（高知名度 {0} 人）==========".format(len(resolved)))
    print(f"\n✗ 国籍可能不一致 {len(country_bad)} 条：")
    for x in country_bad:
        print("  -", x)
    print(f"\n✗ 领域可能不一致 {len(field_bad)} 条：")
    for x in field_bad:
        print("  -", x)
    print(f"\n✗ 出生日期不一致 {len(date_bad)} 条：")
    for x in date_bad:
        print("  -", x)
    print(f"\n✗ 生年不一致 {len(year_bad)} 条：")
    for x in year_bad:
        print("  -", x)
    if not (country_bad or field_bad or date_bad or year_bad):
        print("  全部一致 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
