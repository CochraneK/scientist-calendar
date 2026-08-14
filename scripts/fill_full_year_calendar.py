from __future__ import annotations

import calendar
import json
import os
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests
from opencc import OpenCC
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "app" / "page.tsx"
DATA = ROOT / "app" / "scientists.json"
QUOTES = ROOT / "app" / "quotes.json"

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIQUOTE_API = "https://en.wikiquote.org/w/api.php"
HEADERS = {"User-Agent": "scientist-calendar/1.0 (Codex local generator)"}
SKIP_WIKIQUOTE = os.environ.get("SCIENTIST_CALENDAR_SKIP_WIKIQUOTE") == "1"

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
RELATION_BY_OCC = {
    "Q169470": "物理纪念",
    "Q593644": "化学纪念",
    "Q170790": "数学纪念",
    "Q11063": "宇宙纪念",
    "Q864503": "生命纪念",
    "Q82594": "计算纪念",
    "Q39631": "医学纪念",
    "Q81096": "工程纪念",
    "Q205375": "发明纪念",
}

QUOTE_BY_FIELD = {
    "物理": "规律并不喧哗，它只等被测量。",
    "化学": "变化不是混乱，而是结构在说话。",
    "数学": "抽象不是远离世界，而是逼近本质。",
    "天文": "宇宙的距离，先被耐心量过。",
    "生命科学": "生命最深的答案，常藏在长期观察里。",
    "医学": "知识若不能靠近治愈，就还不够完整。",
    "计算机": "把思想变成系统，才算真正把问题说清。",
    "地球科学": "地球从不沉默，只是需要更长的时间倾听。",
}

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

CURATED_AUTO_OVERRIDES: dict[str, dict[str, str]] = {
    "auto-q211940": {
        "relation": "嗅觉受体与嗅觉系统",
        "field": "生命科学",
        "color": "green",
        "tagline": "从分子层面解释气味如何进入大脑",
        "story": "理查德·阿克塞尔是哥伦比亚大学神经科学家；他与琳达·巴克发现嗅觉受体基因家族，并说明气味信号如何在嗅觉系统中组织，因而共同获得 2004 年诺贝尔生理学或医学奖。",
        "contribution": "嗅觉受体与嗅觉系统组织",
        "fact": "诺贝尔奖公告称，阿克塞尔与巴克的发现解释了气味分子如何被受体识别，以及嗅觉信息如何被送往大脑。",
    }
}

# Hand-edited, source-oriented content is kept in split JSON packs so the
# yearly generator can be rerun without falling back to generic biographies.
for _content_file in sorted((ROOT / "app").glob("curated_content*.json")):
    try:
        _content_payload = json.loads(_content_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _content_payload = {}
    if isinstance(_content_payload, dict):
        CURATED_AUTO_OVERRIDES.update(_content_payload)


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
        return [polish_base_record(record) for record in records if not str(record["id"]).startswith("auto-")]
    return parse_inline_records()


def load_existing_auto_records() -> list[dict[str, Any]]:
    if not DATA.exists():
        return []
    records = json.loads(DATA.read_text(encoding="utf-8"))
    return [polish_generated_record(record) for record in records if str(record["id"]).startswith("auto-")]


def load_curated_quotes() -> dict[str, dict[str, str]]:
    if not QUOTES.exists():
        return {}
    return json.loads(QUOTES.read_text(encoding="utf-8"))


def polish_base_record(record: dict[str, Any]) -> dict[str, Any]:
    polished = dict(record)
    relation = str(polished.get("relation", "")).strip()
    if relation in {"诞辰", "生日", "出生"}:
        polished["relation"] = str(polished.get("contribution") or polished.get("field") or "科学贡献")[:26]
    if polished.get("quoteSource") == "编者整理":
        polished.pop("quote", None)
        polished.pop("quoteSource", None)
    if not quote_source_matches_record(polished):
        polished.pop("quote", None)
        polished.pop("quoteSource", None)
    return polished


def polish_generated_record(record: dict[str, Any]) -> dict[str, Any]:
    polished = dict(record)
    polished.update(CURATED_AUTO_OVERRIDES.get(str(polished.get("id")), {}))
    relation = str(polished.get("relation", "")).strip()
    if relation in set(RELATION_BY_OCC.values()) or relation.endswith("纪念") or relation in {"诞辰", "生日", "出生"}:
        polished["relation"] = str(polished.get("contribution") or polished.get("field") or "科学贡献")[:26]

    story = str(polished.get("story", ""))
    if "这一天用来记住" in story or "他/她" in story:
        name = str(polished.get("name", "这位人物"))
        field = str(polished.get("field", "科学"))
        country = str(polished.get("country", ""))
        contribution = str(polished.get("contribution", "科学工作"))
        identity = f"{country}的{field}人物" if country and country != "国际" else f"{field}人物"
        polished["story"] = f"{name}是{identity}；本页聚焦{contribution}，把这一天和具体的科学工作联系起来。"
    story = str(polished.get("story", ""))
    if "本页聚焦" in story or "把这一天和具体的科学工作联系起来" in story:
        polished["story"] = "资料待补：当前仅保留姓名、日期与领域，不再使用模板句代替人物介绍；正式版需补入代表成果与可靠来源。"

    fact = str(polished.get("fact", ""))
    if "本条用于覆盖" in fact or not fact:
        latin = str(polished.get("latinName") or polished.get("name") or "该人物")
        polished["fact"] = f"{latin} 是继续查找其论文、传记和档案资料时较稳定的检索名。"
    fact = str(polished.get("fact", ""))
    if "继续查找其论文、传记和档案资料时较稳定的检索名" in fact and str(polished.get("id")) not in CURATED_AUTO_OVERRIDES:
        polished["fact"] = "这条资料尚未完成事实复核；保留在全年日历中，作为后续补充代表成果的占位条目。"

    if polished.get("quoteSource") == "编者整理":
        polished.pop("quote", None)
        polished.pop("quoteSource", None)
    if not quote_source_matches_record(polished):
        polished.pop("quote", None)
        polished.pop("quoteSource", None)
    return polished


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "scientist"


def retry_get(url: str, *, params: dict[str, str], timeout: int = 120) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            if response.status_code == 429:
                time.sleep(45 + attempt * 30)
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:120]}")
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
    for index in range(0, len(qids), 25):
        batch = qids[index : index + 25]
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
        time.sleep(1.2)
    return entities


def query_person_details(qids: list[str]) -> dict[str, dict[str, str]]:
    entities = fetch_entities(qids)
    country_ids: list[str] = []
    for entity in entities.values():
        country_id = first_item_claim(entity, "P27")
        if country_id:
            country_ids.append(country_id)
    country_entities = fetch_entities(sorted(set(country_ids))) if country_ids else {}
    details: dict[str, dict[str, str]] = {}
    for qid, entity in entities.items():
        country_id = first_item_claim(entity, "P27")
        country_entity = country_entities.get(country_id) if country_id else None
        sitelinks = entity.get("sitelinks", {})
        details[qid] = {
            "zh": simplify(entity.get("labels", {}).get("zh", entity.get("labels", {}).get("en", {"value": qid})).get("value", qid)),
            "en": entity.get("labels", {}).get("en", {"value": qid}).get("value", qid),
            "desc": simplify(entity.get("descriptions", {}).get("zh", entity.get("descriptions", {}).get("en", {"value": ""})).get("value", "")),
            "country": simplify((country_entity or {}).get("labels", {}).get("zh", (country_entity or {}).get("labels", {}).get("en", {"value": "国际"})).get("value", "国际")),
            "year": claim_year(entity, "P569") or "",
            "death": claim_year(entity, "P570") or "",
            "enwiki": sitelinks.get("enwiki", {}).get("title", ""),
            "zhwiki": sitelinks.get("zhwiki", {}).get("title", ""),
        }
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
    birth_year = detail.get("year") or str(int(candidate["year"]))
    death_year = detail.get("death") or ""
    years = f"{birth_year}–{death_year}" if death_year else f"{birth_year}–"
    relation = detail.get("desc") or f"{occ_name} · {contribution}"
    if len(relation) > 26:
        relation = relation[:26]
    identity = f"{country_name}的{occ_name}" if country_name != "国际" else occ_name
    story_core = detail.get("desc") or f"{zh_name}通常被介绍为{identity}。"
    if contribution not in story_core:
        story_core = f"{story_core.rstrip('。')}，本页以{contribution}作为理解其工作的入口。"
    story_core = story_core.replace("，。", "。")
    if not detail.get("desc"):
        story_core = "资料待补：当前仅保留姓名、日期与领域，不再使用模板句代替人物介绍；正式版需补入代表成果与可靠来源。"
    fact = detail.get("desc")
    if fact:
        fact = f"百科条目将其概括为：{fact[:42]}。"
    else:
        fact = f"{zh_name}的英文条目名为 {en_name}，可据此继续查找其传记与原始资料。"
    record = {
        "id": f"auto-{candidate['qid'].lower()}",
        "month": month,
        "day": day,
        "name": zh_name,
        "latinName": en_name,
        "years": years,
        "field": field,
        "country": country_name,
        "color": color,
        "relation": relation,
        "tagline": tagline,
        "story": story_core,
        "contribution": contribution,
        "fact": fact,
        "quote": None,
        "quoteSource": None,
    }
    record.update(CURATED_AUTO_OVERRIDES.get(record["id"], {}))
    return record


def enrich_quote(record: dict[str, Any], curated_quotes: dict[str, dict[str, str]]) -> dict[str, Any]:
    if record["id"] in curated_quotes:
        return record
    if record.get("quote") and record.get("quoteSource") and record.get("quoteSource") != "编者整理":
        return record
    quote = fetch_wikiquote_quote(str(record.get("latinName") or record.get("name") or ""))
    enriched = dict(record)
    if quote:
        enriched["quote"] = quote["text"]
        enriched["quoteSource"] = quote["source"]
    else:
        enriched.pop("quote", None)
        enriched.pop("quoteSource", None)
    return enriched


def enrich_missing_quotes(records: list[dict[str, Any]], curated_quotes: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    enriched_records = [dict(record) for record in records]
    if SKIP_WIKIQUOTE:
        return enriched_records
    targets: list[tuple[int, str]] = []
    for index, record in enumerate(enriched_records):
        if record["id"] in curated_quotes:
            continue
        if record.get("quote") and record.get("quoteSource") and record.get("quoteSource") != "编者整理":
            continue
        record.pop("quote", None)
        record.pop("quoteSource", None)
        name = str(record.get("latinName") or record.get("name") or "").strip()
        if name:
            targets.append((index, name))

    if not targets:
        return enriched_records

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_wikiquote_quote, name): index for index, name in targets}
        for future in as_completed(futures):
            index = futures[future]
            try:
                quote = future.result()
            except Exception:
                quote = None
            if quote:
                enriched_records[index]["quote"] = quote["text"]
                enriched_records[index]["quoteSource"] = quote["source"]
    return enriched_records


def fetch_wikiquote_quote(name: str) -> dict[str, str] | None:
    if not name:
        return None
    response = wikiquote_get(
        {
            "action": "query",
            "list": "search",
            "srsearch": name,
            "format": "json",
            "srlimit": "5",
        }
    )
    if response is None:
        return None
    results = response.json().get("query", {}).get("search", [])
    exact_titles = [result.get("title", "") for result in results if wikiquote_title_matches(name, result.get("title", ""))]
    titles = []
    if wikiquote_title_matches(name, name):
        titles.append(name)
    titles.extend(title for title in exact_titles if title not in titles)
    for title in titles:
        parse_response = wikiquote_get(
            {
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "redirects": "1",
            }
        )
        if parse_response is None:
            continue
        parse = parse_response.json()
        html = parse.get("parse", {}).get("text", {}).get("*", "")
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for li in soup.select("li"):
            text = " ".join(li.get_text(" ", strip=True).split())
            if not text:
                continue
            if text.startswith(("Repeated", "From ", "See ", "Category:", "Retrieved")):
                continue
            cleaned = clean_quote_text(text)
            if len(cleaned) < 20:
                continue
            return {"text": cleaned, "source": f"Wikiquote · {title}"}
    return None


def quote_source_matches_record(record: dict[str, Any]) -> bool:
    source = str(record.get("quoteSource") or "")
    if not source or not source.startswith("Wikiquote"):
        return True
    title = source.split("·", 1)[-1].strip()
    name = str(record.get("latinName") or record.get("name") or "")
    return wikiquote_title_matches(name, title)


def wikiquote_title_matches(name: str, title: str) -> bool:
    name_key = normalize_title(name)
    title_key = normalize_title(title)
    if not name_key or not title_key:
        return False
    return title_key == name_key


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()).strip()


def wikiquote_get(params: dict[str, str]) -> requests.Response | None:
    try:
        response = requests.get(WIKIQUOTE_API, params=params, headers=HEADERS, timeout=8)
        if response.status_code != 200:
            return None
        return response
    except Exception:
        return None


def clean_quote_text(text: str) -> str:
    text = re.sub(r"\[[^\]]*\]", "", text)
    for marker in [
        "Repeated throughout his life",
        "Repeated throughout her life",
        "commonly quoted as",
        "What he exclaimed",
        "What she exclaimed",
        "as quoted by",
        "Said to be",
        "From ",
        "see: Quote Investigator",
    ]:
        if marker in text:
            text = text.split(marker, 1)[0].strip(" ,;:")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:180]


def main() -> None:
    curated_quotes = load_curated_quotes()
    base = [polish_base_record(record) for record in load_base_records()]
    covered = {(int(item["month"]), int(item["day"])) for item in base}
    missing = [(m, d) for m in range(1, 13) for d in range(1, calendar.monthrange(2026, m)[1] + 1) if (m, d) not in covered]

    existing_by_date = {(int(record["month"]), int(record["day"])): record for record in load_existing_auto_records()}
    if missing and all(key in existing_by_date for key in missing):
        additions = [existing_by_date[key] for key in missing]
        source_note = "existing full-year dataset"
    else:
        try:
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
            additions = [make_record(candidate, details.get(candidate["qid"], {})) for candidate in chosen]
            source_note = "Wikidata"
        except Exception as error:  # noqa: BLE001 - use the existing full-year dataset if Wikidata is rate-limited
            additions = [existing_by_date[key] for key in missing if key in existing_by_date]
            if len(additions) != len(missing):
                raise RuntimeError(f"Could not rebuild all missing dates after Wikidata failure: {error}") from error
            source_note = "existing full-year dataset"

    combined = enrich_missing_quotes(base + additions, curated_quotes)
    combined = sorted(combined, key=lambda item: (int(item["month"]), int(item["day"]), item["name"]))
    DATA.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    unique_dates = {(int(item["month"]), int(item["day"])) for item in combined}
    print(f"Wrote {len(combined)} records covering {len(unique_dates)} dates using {source_note}")


if __name__ == "__main__":
    main()
