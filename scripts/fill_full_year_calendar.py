from __future__ import annotations

import calendar
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

import requests
from opencc import OpenCC


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "app" / "page.tsx"
DATA = ROOT / "app" / "scientists.json"

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
HEADERS = {"User-Agent": "scientist-calendar/1.0 (Codex local generator)"}

FIELDS = {
    "Q169470": ("物理", "blue", "在物质与能量之间寻找可验证的规律", "物理学研究"),
    "Q593644": ("化学", "green", "把物质变化拆解成可以理解的结构", "化学研究"),
    "Q170790": ("数学", "violet", "用抽象语言整理世界的结构", "数学研究"),
    "Q11063": ("天文", "gold", "把目光投向更辽阔的宇宙尺度", "天文学研究"),
    "Q864503": ("生命科学", "green", "在生命现象中寻找秩序与证据", "生物学研究"),
    "Q82594": ("计算机", "coral", "把问题转化为机器可以执行的逻辑", "计算机科学"),
    "Q39631": ("医学", "green", "让疾病与治疗进入更精确的知识体系", "医学实践与研究"),
    "Q81096": ("物理", "blue", "把科学原理落到可以工作的工程之中", "工程实践"),
    "Q205375": ("物理", "coral", "把新的想法变成可使用的工具", "发明与工程"),
}

DEFAULT_FIELD = ("生命科学", "gold", "用系统方法追问自然世界的规律", "科学研究")
CONVERTER = OpenCC("t2s")

OCCUPATION_LABELS = {
    "Q169470": "物理学家",
    "Q593644": "化学家",
    "Q170790": "数学家",
    "Q11063": "天文学家",
    "Q864503": "生物学家",
    "Q82594": "计算机科学家",
    "Q39631": "医生",
    "Q81096": "工程师",
    "Q205375": "发明家",
    "Q901": "科学家",
}


def parse_inline_records() -> list[dict[str, Any]]:
    source = PAGE.read_text(encoding="utf-8")
    objects = re.findall(r'\{ id: "(?P<id>[^"]+)", (?P<body>.*?) \}(?:,|(?=\n\s*\]))', source, re.S)
    required = ("month", "day", "name", "latinName", "years", "field", "country", "color", "relation", "tagline", "story", "contribution", "fact")
    records: list[dict[str, Any]] = []
    for item_id, body in objects:
        record: dict[str, Any] = {"id": item_id}
        for key, value in re.findall(r'(\w+): "([^"]*)"', body):
            record[key] = value
        for key, value in re.findall(r'(month|day): (\d+)', body):
            record[key] = int(value)
        if all(key in record for key in required):
            records.append(record)
    return records


def load_base_records() -> list[dict[str, Any]]:
    if DATA.exists():
        records = json.loads(DATA.read_text(encoding="utf-8"))
        return [record for record in records if not str(record["id"]).startswith("auto-")]
    return parse_inline_records()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "scientist"


def retry_get(url: str, *, params: dict[str, str], timeout: int = 120) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            if response.status_code in {429, 500, 502, 503, 504}:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:120]}")
            response.raise_for_status()
            return response
        except Exception as error:  # noqa: BLE001 - network retries are intentional here
            last_error = error
            time.sleep(2 + attempt * 3)
    raise RuntimeError(f"Request failed after retries: {last_error}")


def query_candidates() -> list[dict[str, str]]:
    occupations = " ".join(f"wd:{qid}" for qid in FIELDS)
    query = f"""SELECT ?person ?dob ?occ ?sitelinks WHERE {{
  VALUES ?occ {{ {occupations} }}
  ?person wdt:P31 wd:Q5;
          wdt:P569 ?dob;
          wdt:P106 ?occ;
          wikibase:sitelinks ?sitelinks.
}} LIMIT 20000"""
    response = retry_get(WIKIDATA_SPARQL, params={"format": "json", "query": query}, timeout=180)
    rows = response.json()["results"]["bindings"]
    candidates: list[dict[str, str]] = []
    for row in rows:
        person = row["person"]["value"].rsplit("/", 1)[-1]
        occ = row["occ"]["value"].rsplit("/", 1)[-1]
        dob = row["dob"]["value"]
        match = re.match(r"(-?\d{1,6})-(\d{2})-(\d{2})", dob)
        if not match:
            continue
        year, month, day = match.groups()
        if (month, day) == ("02", "29"):
            continue
        sitelinks = row.get("sitelinks", {}).get("value", "0")
        candidates.append({"qid": person, "occ": occ, "year": year, "month": month, "day": day, "sitelinks": sitelinks})
    return candidates


def fetch_entities(qids: list[str]) -> dict[str, dict[str, Any]]:
    entities: dict[str, dict[str, Any]] = {}
    for index in range(0, len(qids), 50):
        batch = qids[index : index + 50]
        response = retry_get(
            WIKIDATA_API,
            params={
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "labels|descriptions|claims",
                "languages": "zh|en",
                "format": "json",
            },
            timeout=60,
        )
        entities.update(response.json().get("entities", {}))
    return entities


def query_person_details(qids: list[str]) -> dict[str, dict[str, str]]:
    values = " ".join(f"wd:{qid}" for qid in qids)
    query = f"""SELECT ?person ?zhLabel ?enLabel ?countryZh ?countryEn ?dod WHERE {{
  VALUES ?person {{ {values} }}
  OPTIONAL {{ ?person rdfs:label ?zhLabel FILTER(LANG(?zhLabel) = "zh") }}
  OPTIONAL {{ ?person rdfs:label ?enLabel FILTER(LANG(?enLabel) = "en") }}
  OPTIONAL {{ ?person wdt:P570 ?dod. }}
  OPTIONAL {{
    ?person wdt:P27 ?country.
    OPTIONAL {{ ?country rdfs:label ?countryZh FILTER(LANG(?countryZh) = "zh") }}
    OPTIONAL {{ ?country rdfs:label ?countryEn FILTER(LANG(?countryEn) = "en") }}
  }}
}}"""
    response = retry_get(WIKIDATA_SPARQL, params={"format": "json", "query": query}, timeout=180)
    details: dict[str, dict[str, str]] = {}
    for row in response.json()["results"]["bindings"]:
        qid = row["person"]["value"].rsplit("/", 1)[-1]
        if qid in details:
            continue
        detail: dict[str, str] = {
            "zh": simplify(row.get("zhLabel", {}).get("value", "")),
            "en": row.get("enLabel", {}).get("value", ""),
            "country": simplify(row.get("countryZh", row.get("countryEn", {})).get("value", "")),
            "dod": row.get("dod", {}).get("value", ""),
        }
        details[qid] = detail
    return details


def simplify(text: str) -> str:
    return CONVERTER.convert(text) if text else text


def has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def label(entity: dict[str, Any] | None, fallback: str) -> str:
    if not entity:
        return fallback
    labels = entity.get("labels", {})
    return simplify(labels.get("zh", labels.get("en", {"value": fallback})).get("value", fallback))


def english_label(entity: dict[str, Any] | None, fallback: str) -> str:
    if not entity:
        return fallback
    return entity.get("labels", {}).get("en", {"value": fallback}).get("value", fallback)


def description(entity: dict[str, Any] | None) -> str:
    if not entity:
        return ""
    descriptions = entity.get("descriptions", {})
    return descriptions.get("zh", descriptions.get("en", {"value": ""})).get("value", "")


def claim_year(entity: dict[str, Any] | None, prop: str) -> str | None:
    if not entity:
        return None
    claims = entity.get("claims", {}).get(prop, [])
    for claim in claims:
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(value, dict) and "time" in value:
            match = re.match(r"[+-](\d{4,6})", value["time"])
            if match:
                return str(int(match.group(1)))
    return None


def first_item_claim(entity: dict[str, Any] | None, prop: str) -> str | None:
    if not entity:
        return None
    claims = entity.get("claims", {}).get(prop, [])
    for claim in claims:
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(value, dict) and "id" in value:
            return value["id"]
    return None


def make_record(candidate: dict[str, str], detail: dict[str, str]) -> dict[str, Any]:
    occ_id = candidate["occ"]
    field, color, tagline, contribution = FIELDS.get(occ_id, DEFAULT_FIELD)
    zh_name = simplify(detail.get("zh") or detail.get("en") or candidate["qid"])
    en_name = detail.get("en") or zh_name
    occ_name = OCCUPATION_LABELS.get(occ_id, "科学家")
    country_name = detail.get("country") or "国际"
    if not has_cjk(country_name):
        country_name = "国际"
    month = int(candidate["month"])
    day = int(candidate["day"])
    birth_year = str(int(candidate["year"]))
    death_year = None
    death_date = detail.get("dod") or ""
    match = re.match(r"[+-](\d{4,6})", death_date)
    if match:
        death_year = str(int(match.group(1)))
    years = f"{birth_year}–{death_year}" if death_year else f"{birth_year}–"
    story_core = f"{zh_name}是{country_name}的{occ_name}，本页作为 {month} 月 {day} 日的科学人物索引，后续可继续补充代表性成果与原始资料。"
    return {
        "id": f"auto-{candidate['qid'].lower()}",
        "month": month,
        "day": day,
        "name": zh_name,
        "latinName": en_name,
        "years": years,
        "field": field,
        "country": country_name,
        "color": color,
        "relation": "诞辰",
        "tagline": tagline,
        "story": story_core,
        "contribution": contribution,
        "fact": f"Wikidata 公开资料记录其生日为 {month} 月 {day} 日；本条用于补齐全年日期覆盖。",
    }


def main() -> None:
    base = load_base_records()
    covered = {(int(item["month"]), int(item["day"])) for item in base}
    missing = [(m, d) for m in range(1, 13) for d in range(1, calendar.monthrange(2026, m)[1] + 1) if (m, d) not in covered]
    if not missing:
        DATA.write_text(json.dumps(sorted(base, key=lambda item: (item["month"], item["day"], item["name"])), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Already full year: {len(base)} records")
        return

    candidates = query_candidates()
    by_date: dict[tuple[int, int], list[dict[str, str]]] = {}
    for candidate in candidates:
        key = (int(candidate["month"]), int(candidate["day"]))
        if key in missing:
            by_date.setdefault(key, []).append(candidate)

    chosen: list[dict[str, str]] = []
    used_qids = set()
    for key in missing:
        options = sorted(by_date.get(key, []), key=lambda item: int(item.get("sitelinks", 0)), reverse=True)
        if not options:
            raise RuntimeError(f"No Wikidata candidate for {key[0]:02d}-{key[1]:02d}")
        candidate = next((item for item in options if item["qid"] not in used_qids), options[0])
        used_qids.add(candidate["qid"])
        chosen.append(candidate)

    details = query_person_details([item["qid"] for item in chosen])

    additions: list[dict[str, Any]] = []
    for candidate in chosen:
        additions.append(make_record(candidate, details.get(candidate["qid"], {})))

    combined = sorted(base + additions, key=lambda item: (int(item["month"]), int(item["day"]), item["name"]))
    DATA.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    unique_dates = {(int(item["month"]), int(item["day"])) for item in combined}
    print(f"Wrote {len(combined)} records covering {len(unique_dates)} dates")


if __name__ == "__main__":
    main()
