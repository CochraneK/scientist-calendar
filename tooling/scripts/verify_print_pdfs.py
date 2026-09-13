from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCIENTISTS_PATH = ROOT / "app" / "data" / "scientists.json"
VERIFY_SCRIPT = ROOT / "tooling" / "scripts" / "verify_pdf_layout.py"
PRINT_DIR = ROOT / "public" / "print"


def main() -> int:
    scientists = json.loads(SCIENTISTS_PATH.read_text(encoding="utf-8"))
    pdfs = [
        PRINT_DIR / f"科学家日历_精选{len(scientists)}位_A4打印版.pdf",
        PRINT_DIR / "科学家日历_月度生日版_A4.pdf",
    ]

    missing = [path for path in pdfs if not path.is_file()]
    if missing:
        for path in missing:
            print(f"Missing published PDF: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1

    for pdf in pdfs:
        print(f"Verifying {pdf.relative_to(ROOT)}")
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(VERIFY_SCRIPT), str(pdf), "--quiet"],
            cwd=ROOT,
            check=False,
        )
        if result.returncode:
            return result.returncode

    print("✓ Published PDF artifacts passed layout/tofu verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
