from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCIENTISTS_PATH = ROOT / "app" / "data" / "scientists.json"
QUOTES_PATH = ROOT / "app" / "data" / "quotes.json"
INDEX_PATH = ROOT / "app" / "data" / "scientists-index.json"
DETAILS_DIR = ROOT / "app" / "data" / "details"

INDEX_FIELDS = (
    "id",
    "month",
    "day",
    "name",
    "latinName",
    "years",
    "field",
    "country",
    "color",
    "relation",
    "tagline",
    "contribution",
)


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def build_outputs() -> dict[Path, str]:
    scientists = json.loads(SCIENTISTS_PATH.read_text(encoding="utf-8"))
    quotes = json.loads(QUOTES_PATH.read_text(encoding="utf-8"))

    index: list[dict[str, object]] = []
    details_by_month: dict[int, dict[str, object]] = {month: {} for month in range(1, 13)}

    for scientist in scientists:
        index.append({field: scientist[field] for field in INDEX_FIELDS})
        quote = quotes.get(scientist["id"])
        detail: dict[str, object] = {
            "story": scientist["story"],
            "fact": scientist["fact"],
        }
        if quote:
            detail["quote"] = quote["text"]
            detail["quoteSource"] = quote["source"]
        elif scientist.get("quote") and scientist.get("quoteSource"):
            detail["quote"] = scientist["quote"]
            detail["quoteSource"] = scientist["quoteSource"]
        details_by_month[int(scientist["month"])][scientist["id"]] = detail

    outputs = {INDEX_PATH: json_text(index)}
    for month, details in details_by_month.items():
        outputs[DETAILS_DIR / f"{month:02d}.json"] = json_text(details)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate web-optimized scientist index and monthly detail shards.")
    parser.add_argument("--check", action="store_true", help="Fail if generated files are missing or stale.")
    args = parser.parse_args()

    outputs = build_outputs()
    stale: list[str] = []
    for path, expected in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")

    if stale:
        print("Generated web data is stale:")
        for path in stale:
            print(f"- {path}")
        print("Run: python -X utf8 tooling/scripts/build_web_data.py")
        return 1

    if args.check:
        print("✓ Web data shards are up to date")
    else:
        print(f"✓ Generated {len(outputs)} web data files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
