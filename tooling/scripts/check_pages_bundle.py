from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
INDEX = DOCS / "index.html"

MAX_ENTRY_KB = int(os.environ.get("PAGES_MAX_ENTRY_KB", "250"))
MAX_CHUNK_KB = int(os.environ.get("PAGES_MAX_JS_CHUNK_KB", "450"))


def kib(size: int) -> float:
    return size / 1024


def main() -> int:
    if not INDEX.is_file() or not ASSETS.is_dir():
        print("Pages build output is missing; run npm run build:pages first.", file=sys.stderr)
        return 1

    chunks = sorted(ASSETS.glob("*.js"))
    if not chunks:
        print("No JavaScript chunks found in docs/assets.", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in chunks:
        size = path.stat().st_size
        if size > MAX_CHUNK_KB * 1024:
            errors.append(
                f"JS chunk {path.name} is {kib(size):.1f} KiB, above {MAX_CHUNK_KB} KiB"
            )

    html = INDEX.read_text(encoding="utf-8")
    entry_refs = re.findall(r'<script[^>]+src="([^"]+\.js)"', html)
    if not entry_refs:
        errors.append("Could not find the Pages module entry script in docs/index.html")
    else:
        for ref in entry_refs:
            rel = ref.split("/scientist-calendar/", 1)[-1].lstrip("/")
            path = DOCS / rel
            if not path.is_file():
                errors.append(f"Entry script referenced by index.html is missing: {rel}")
                continue
            size = path.stat().st_size
            if size > MAX_ENTRY_KB * 1024:
                errors.append(
                    f"Pages entry {path.name} is {kib(size):.1f} KiB, above {MAX_ENTRY_KB} KiB"
                )

    largest = sorted(((p.stat().st_size, p.name) for p in chunks), reverse=True)[:5]
    print("Largest JS chunks:")
    for size, name in largest:
        print(f"- {name}: {kib(size):.1f} KiB")

    if errors:
        print("\nBundle budget failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"✓ Pages bundle within budget (entry <= {MAX_ENTRY_KB} KiB; any chunk <= {MAX_CHUNK_KB} KiB)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
