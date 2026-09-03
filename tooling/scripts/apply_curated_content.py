from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "app" / "data" / "scientists.json"
PACKS = sorted((ROOT / "app" / "data").glob("curated_content*.json"))


def main() -> None:
    content: dict[str, dict[str, str]] = {}
    for path in PACKS:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            content.update(payload)
    records = json.loads(DATA.read_text(encoding="utf-8"))
    matched = 0
    missing = []
    for record in records:
        key = str(record.get("latinName", ""))
        override = content.get(key)
        if not override:
            if "资料待补" in str(record.get("story", "")):
                missing.append(key)
            continue
        record.update(override)
        matched += 1
    DATA.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"applied={matched} packs={len(PACKS)} missing_placeholders={len(missing)}")
    if missing:
        print("missing:", ", ".join(missing))


if __name__ == "__main__":
    main()
