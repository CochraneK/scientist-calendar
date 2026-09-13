#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prevent avatar provenance debt from growing.

The repository predates per-file attribution metadata for many portraits. Those
existing photos are frozen in tooling/data/legacy-avatars.json. Any photo added
after that baseline must have a complete entry in public/avatar-provenance.json.

This does not pretend the legacy portraits are fully attributed; it only makes
that historical debt explicit while enforcing correct metadata for new work.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AVATARS = ROOT / "public" / "avatars.json"
LEGACY = ROOT / "tooling" / "data" / "legacy-avatars.json"
PROVENANCE = ROOT / "public" / "avatar-provenance.json"
REQUIRED_FIELDS = ("sourceUrl", "author", "license", "licenseUrl", "attribution")


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def is_https_url(value: object) -> bool:
    return isinstance(value, str) and value.startswith("https://") and len(value) > len("https://")


def main() -> int:
    avatars = load_json(AVATARS)
    legacy = load_json(LEGACY)
    provenance = load_json(PROVENANCE)

    if not isinstance(avatars, dict) or not isinstance(legacy, dict) or not isinstance(provenance, dict):
        print("✗ avatars / legacy-avatars / avatar-provenance 必须都是 JSON 对象")
        return 1

    current_photos = {sid for sid, info in avatars.items() if isinstance(info, dict) and info.get("photo") is True}
    legacy_photos = {sid for sid, info in legacy.items() if isinstance(info, dict) and info.get("photo") is True}
    problems: list[str] = []
    complete: set[str] = set()

    for sid, payload in sorted(provenance.items()):
        if sid not in avatars:
            problems.append(f"avatar-provenance.json 指向未知人物：{sid}")
        if not isinstance(payload, dict):
            problems.append(f"avatar-provenance.json[{sid}] 必须是对象")
            continue

        missing = [field for field in REQUIRED_FIELDS if not isinstance(payload.get(field), str) or not payload[field].strip()]
        if missing:
            problems.append(f"avatar-provenance.json[{sid}] 缺少字段：{', '.join(missing)}")
            continue
        if not is_https_url(payload.get("sourceUrl")):
            problems.append(f"avatar-provenance.json[{sid}].sourceUrl 必须是 https URL")
            continue
        if not is_https_url(payload.get("licenseUrl")):
            problems.append(f"avatar-provenance.json[{sid}].licenseUrl 必须是 https URL")
            continue
        complete.add(sid)

    # Legacy photo IDs may remain unattributed while the historical backlog is
    # researched. Any new photo must be fully attributed in the same change.
    new_unattributed = sorted(current_photos - legacy_photos - complete)
    if new_unattributed:
        preview = "、".join(new_unattributed[:20])
        suffix = "…" if len(new_unattributed) > 20 else ""
        problems.append(
            f"新增照片缺少完整 provenance（{len(new_unattributed)}）：{preview}{suffix}"
        )

    covered_current = current_photos & complete
    grandfathered = current_photos & legacy_photos - complete
    print(
        f"头像照片：{len(current_photos)}　完整 provenance：{len(covered_current)}　"
        f"历史待补：{len(grandfathered)}"
    )

    if problems:
        print(f"✗ 来源治理错误 {len(problems)} 条：")
        for problem in problems:
            print("  -", problem)
        return 1

    print("✓ 未新增无来源照片；历史 provenance 债务未扩大")
    return 0


if __name__ == "__main__":
    sys.exit(main())
