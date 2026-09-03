#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把正文里的半角标点改成中文全角标点。

规则（保守，避免误伤拉丁文与数字）：
  - 逐字符扫描，遇到 , ; : ? ! 时：
      * 前后都是数字（千分位，如 1,000）→ 不动
      * 前一个字符是 ASCII 字母、后一个字符是空格（拉丁文列举，如 "Pulse, Grimace"）→ 不动
      * 其余一律转为全角
  - 遇到 ( ) 时：只要紧邻的一侧是中日韩字符就转成全角括号
  - latinName 与 years 字段整体跳过（纯拉丁文 / 纯数字区间）

用法：
  python -X utf8 scripts/fix_punctuation.py          # 直接改写文件
  python -X utf8 scripts/fix_punctuation.py --dry    # 只打印将要改动的条目
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCIENTISTS = ROOT / "app" / "data" / "scientists.json"
QUOTES = ROOT / "app" / "data" / "quotes.json"

# 需要转换的半角标点 -> 全角
PAIR = {",": "，", ";": "；", ":": "：", "?": "？", "!": "！"}
PAREN = {"(": "（", ")": "）"}

SKIP_FIELDS = {"latinName", "years"}
TEXT_FIELDS = ["name", "country", "relation", "tagline", "story", "contribution", "fact"]


def is_cjk(char: str) -> bool:
    if not char:
        return False
    code = ord(char)
    return (
        0x4E00 <= code <= 0x9FFF      # CJK 统一表意文字
        or 0x3000 <= code <= 0x303F   # 中文标点
        or 0xFF00 <= code <= 0xFFEF   # 全角字符
    )


def is_ascii_letter(char: str) -> bool:
    return bool(char) and char.isascii() and char.isalpha()


def fix(text: str) -> str:
    # 第一遍：, ; : ? ! —— 先把逗号等做成全角，第二遍判断括号时才有正确的邻居字符。
    chars = list(text)
    for index, char in enumerate(chars):
        prev = chars[index - 1] if index > 0 else ""
        nxt = chars[index + 1] if index + 1 < len(chars) else ""

        if char in PAIR:
            if prev.isdigit() and nxt.isdigit():
                continue                                   # 千分位
            if is_ascii_letter(prev) and nxt == " ":
                continue                                   # 拉丁文列举
            chars[index] = PAIR[char]
    text = "".join(chars)

    # 第二遍：( ) —— 只要紧邻的一侧是中日韩字符（含刚转换出的全角标点）就转全角括号。
    chars = list(text)
    for index, char in enumerate(chars):
        prev = chars[index - 1] if index > 0 else ""
        nxt = chars[index + 1] if index + 1 < len(chars) else ""
        if char in PAREN and (is_cjk(prev) or is_cjk(nxt)):
            chars[index] = PAREN[char]
    return "".join(chars)


def process(path: Path, mutate: bool) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    changed = 0

    if isinstance(payload, list):
        for entry in payload:
            for key in TEXT_FIELDS:
                value = entry.get(key)
                if key in SKIP_FIELDS or not isinstance(value, str):
                    continue
                new = fix(value)
                if new != value:
                    changed += 1
                    print(f"  {entry.get('id')}/{key}:\n    - {value}\n    + {new}")
                    entry[key] = new
    elif isinstance(payload, dict):
        for key, entry in payload.items():
            if not isinstance(entry, dict):
                continue
            for field in ("text", "source"):
                value = entry.get(field)
                if not isinstance(value, str):
                    continue
                new = fix(value)
                if new != value:
                    changed += 1
                    print(f"  quotes[{key}]/{field}:\n    - {value}\n    + {new}")
                    entry[field] = new

    if mutate and changed:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    mutate = "--dry" not in sys.argv
    print(f"模式：{'写入' if mutate else '预览'}\n")

    total = 0
    for path in (SCIENTISTS, QUOTES):
        print(f"=== {path.relative_to(ROOT)} ===")
        total += process(path, mutate)
        print()

    print(f"共修订 {total} 处")
    return 0


if __name__ == "__main__":
    sys.exit(main())
