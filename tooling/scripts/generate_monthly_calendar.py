#!/usr/bin/env python3
"""《科学家日历 · 月度生日版》A4 PDF 生成入口。

统一委托至 theme-calendar-factory 通用引擎（由根目录 theme.json 驱动），
杜绝项目脚本与通用模板分叉。保留此包装脚本以兼容现有 npm 脚本与 CI 工作流。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "tooling" / "skills" / "theme-calendar-factory" / "scripts" / "generate_monthly_pdf.py"
CONFIG = ROOT / "theme.json"


def main() -> int:
    cmd = [sys.executable, "-X", "utf8", str(ENGINE), "--config", str(CONFIG), *sys.argv[1:]]
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
