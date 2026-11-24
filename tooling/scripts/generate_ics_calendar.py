#!/usr/bin/env python3
"""《科学家日历》365 天 RFC 5545 (.ics) 订阅日历生成/校验入口。

统一委托至 theme-calendar-factory 通用引擎（由根目录 theme.json 驱动），
杜绝项目脚本与通用模板分叉。保留此包装脚本以兼容 npm run build:ics / check:ics 与 CI。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "tooling" / "skills" / "theme-calendar-factory" / "scripts" / "generate_ics.py"
CONFIG = ROOT / "theme.json"


def main() -> int:
    cmd = [sys.executable, "-X", "utf8", str(ENGINE), "--config", str(CONFIG), *sys.argv[1:]]
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
