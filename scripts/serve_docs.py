#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地预览构建产物（docs/）。

静态站以 `/scientist-calendar/` 为 base 路径，直接用 `python -m http.server`
打开 docs/index.html 会因为资源路径不对而白屏。本脚本把该前缀映射到 docs/。

用法：python -X utf8 scripts/serve_docs.py [端口，默认 8765]
访问：http://localhost:8765/scientist-calendar/
"""

from __future__ import annotations

import http.server
import sys
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BASE = "/scientist-calendar"


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        # 去掉 base 前缀后再映射到 docs/
        if path == BASE or path.startswith(f"{BASE}/"):
            path = path[len(BASE):] or "/"
        return super().translate_path(path)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    if not DOCS.exists():
        print("docs/ 不存在，请先运行 npm run build:pages")
        return 1
    print(f"预览: http://localhost:{port}{BASE}/")
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", port), partial(Handler, directory=str(DOCS))
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
