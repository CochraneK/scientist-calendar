#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic provenance guard for scientist facts.

Existing content is frozen as a hash baseline. Future changes to factual field groups must
be accompanied by one or more source records whose `covers` union includes every changed
group. This avoids pretending legacy content is already fully sourced while preventing the
unsourced debt from growing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "app" / "data" / "scientists.json"
SOURCES = ROOT / "app" / "data" / "scientist-sources.json"
BASELINE = ROOT / "tooling" / "data" / "legacy-scientist-facts.json"

GROUPS: dict[str, tuple[str, ...]] = {
    "identity": ("name", "latinName", "field", "country"),
    "dates": ("month", "day", "years"),
    "profile": ("relation", "tagline"),
    "story": ("story",),
    "contribution": ("contribution",),
    "fact": ("fact",),
}
ALLOWED_GROUPS = set(GROUPS)
REQUIRED_SOURCE_FIELDS = ("title", "publisher", "url", "covers")


def load_json(path: Path):
    if not path.exists():
        raise SystemExit(f"缺少文件：{path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_group_payload(scientist: dict, fields: tuple[str, ...]) -> bytes:
    payload = {field: scientist.get(field) for field in fields}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def group_hash(scientist: dict, fields: tuple[str, ...]) -> str:
    return hashlib.sha256(canonical_group_payload(scientist, fields)).hexdigest()


def snapshot(scientists: list[dict]) -> dict:
    return {
        "version": 1,
        "algorithm": "sha256-json-v1",
        "groups": {name: list(fields) for name, fields in GROUPS.items()},
        "scientists": {
            scientist["id"]: {name: group_hash(scientist, fields) for name, fields in GROUPS.items()}
            for scientist in sorted(scientists, key=lambda item: item["id"])
        },
    }


def validate_sources(scientists_by_id: dict[str, dict], source_doc: dict) -> tuple[dict[str, set[str]], list[str]]:
    errors: list[str] = []
    coverage: dict[str, set[str]] = {}

    if source_doc.get("version") != 1:
        errors.append("scientist-sources.json: version 必须为 1")
    registry = source_doc.get("scientists")
    if not isinstance(registry, dict):
        return coverage, errors + ["scientist-sources.json: scientists 必须是对象"]

    for scientist_id, records in registry.items():
        if scientist_id not in scientists_by_id:
            errors.append(f"sources[{scientist_id}]: 对应人物不存在")
            continue
        if not isinstance(records, list) or not records:
            errors.append(f"sources[{scientist_id}]: 至少需要 1 条来源记录")
            continue

        seen_urls: set[str] = set()
        scientist_coverage: set[str] = set()
        for index, record in enumerate(records, start=1):
            prefix = f"sources[{scientist_id}][{index}]"
            if not isinstance(record, dict):
                errors.append(f"{prefix}: 必须是对象")
                continue
            missing = [field for field in REQUIRED_SOURCE_FIELDS if field not in record]
            if missing:
                errors.append(f"{prefix}: 缺少字段 {', '.join(missing)}")
                continue

            for field in ("title", "publisher", "url"):
                if not isinstance(record.get(field), str) or not record[field].strip():
                    errors.append(f"{prefix}.{field}: 必须是非空字符串")

            raw_url = record.get("url", "")
            parsed = urlparse(raw_url) if isinstance(raw_url, str) else None
            if not parsed or parsed.scheme not in {"http", "https"} or not parsed.netloc:
                errors.append(f"{prefix}.url: 必须是可追溯的 http/https URL")
            elif raw_url in seen_urls:
                errors.append(f"{prefix}.url: 同一人物不能重复登记相同 URL")
            else:
                seen_urls.add(raw_url)

            covers = record.get("covers")
            if not isinstance(covers, list) or not covers:
                errors.append(f"{prefix}.covers: 至少覆盖 1 个字段组")
                continue
            if len(covers) != len(set(covers)):
                errors.append(f"{prefix}.covers: 不允许重复字段组")
            invalid = sorted(set(covers) - ALLOWED_GROUPS)
            if invalid:
                errors.append(f"{prefix}.covers: 未知字段组 {', '.join(invalid)}")
            scientist_coverage.update(group for group in covers if group in ALLOWED_GROUPS)

            notes = record.get("notes")
            if notes is not None and (not isinstance(notes, str) or not notes.strip()):
                errors.append(f"{prefix}.notes: 若提供则必须是非空字符串")

        coverage[scientist_id] = scientist_coverage

    return coverage, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="科学家事实来源与历史债务门禁")
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="写入当前事实哈希作为治理基线；只用于首次启用或经过审查的基线迁移",
    )
    args = parser.parse_args()

    scientists = load_json(DATA)
    if not isinstance(scientists, list):
        raise SystemExit("scientists.json 顶层必须是数组")
    ids = [item.get("id") for item in scientists]
    if any(not isinstance(scientist_id, str) or not scientist_id for scientist_id in ids):
        raise SystemExit("scientists.json 中存在空/非法 id")
    if len(ids) != len(set(ids)):
        raise SystemExit("scientists.json 中存在重复 id")
    scientists_by_id = {item["id"]: item for item in scientists}

    source_doc = load_json(SOURCES)
    coverage, errors = validate_sources(scientists_by_id, source_doc)

    if args.write_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(
            json.dumps(snapshot(scientists), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"✓ 已写入事实治理基线：{len(scientists)} 人 × {len(GROUPS)} 字段组")
        if errors:
            for error in errors:
                print(f"✗ {error}")
            return 1
        return 0

    baseline = load_json(BASELINE)
    if baseline.get("version") != 1 or baseline.get("algorithm") != "sha256-json-v1":
        errors.append("legacy-scientist-facts.json: 不支持的 version/algorithm")
    if baseline.get("groups") != {name: list(fields) for name, fields in GROUPS.items()}:
        errors.append("legacy-scientist-facts.json: 字段组定义与审计脚本不一致")

    legacy = baseline.get("scientists")
    if not isinstance(legacy, dict):
        errors.append("legacy-scientist-facts.json: scientists 必须是对象")
        legacy = {}

    current_ids = set(scientists_by_id)
    legacy_ids = set(legacy)
    deleted = sorted(legacy_ids - current_ids)
    if deleted:
        errors.append(
            "检测到历史人物被删除；如属有意数据迁移，请单独审查并重建基线：" + ", ".join(deleted[:20])
        )

    changed_summary: list[tuple[str, list[str]]] = []
    for scientist_id, scientist in scientists_by_id.items():
        baseline_hashes = legacy.get(scientist_id)
        if baseline_hashes is None:
            changed_groups = sorted(ALLOWED_GROUPS)
        elif not isinstance(baseline_hashes, dict):
            errors.append(f"baseline[{scientist_id}]: 格式非法")
            continue
        else:
            changed_groups = [
                name
                for name, fields in GROUPS.items()
                if baseline_hashes.get(name) != group_hash(scientist, fields)
            ]

        if not changed_groups:
            continue
        changed_summary.append((scientist_id, changed_groups))
        covered = coverage.get(scientist_id, set())
        missing_coverage = sorted(set(changed_groups) - covered)
        if missing_coverage:
            errors.append(
                f"{scientist_id}: 修改了字段组 {', '.join(changed_groups)}，"
                f"但来源未覆盖 {', '.join(missing_coverage)}"
            )

    sourced_people = sum(1 for groups in coverage.values() if groups)
    fully_sourced = sum(1 for groups in coverage.values() if groups >= ALLOWED_GROUPS)
    legacy_unsourced = len(scientists) - sourced_people
    print(
        f"人物：{len(scientists)}　有来源登记：{sourced_people}　"
        f"全字段覆盖：{fully_sourced}　历史待补：{legacy_unsourced}"
    )
    if changed_summary:
        for scientist_id, groups in changed_summary[:20]:
            print(f"变更：{scientist_id} -> {', '.join(groups)}")
        if len(changed_summary) > 20:
            print(f"…另有 {len(changed_summary) - 20} 人发生事实变更")

    if errors:
        print("\n事实来源审计失败：")
        for error in errors:
            print(f"✗ {error}")
        return 1

    print("✓ 未发现无来源事实变更；历史来源债务未扩大")
    return 0


if __name__ == "__main__":
    sys.exit(main())
