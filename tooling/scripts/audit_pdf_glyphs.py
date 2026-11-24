#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 字体字符集自检：找出被 CID 字体静默丢弃 / 破坏的字符。

为什么需要它：
  reportlab 的 STSong-Light(Adobe-GB1 CID) 对很多字符**不报错、不吐豆腐块**，
  而是直接丢字或把文本流截断——例如 `6.02×10²³` 会渲染成 `6.02×10`（数值直接错掉），
  `François` 会变成 `Franois`。肉眼抽查永远抓不全。

  正确做法：把数据里出现的每一个非 ASCII 字符单独渲染进 PDF，再抽回来逐个比对，
  得到「哪些字符会被静默丢弃」的权威清单，据此在生成器的 _fix_dot() 里补映射。

用法：
  python -X utf8 tooling/scripts/audit_pdf_glyphs.py app/data/scientists.json app/data/quotes.json
  python -X utf8 tooling/scripts/audit_pdf_glyphs.py --allow ²³⁻  # 声明这些字符已在生成器里转写

退出码：0 = 无未处理字符；1 = 存在会被静默丢弃的字符（CI 可拦截）。
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def collect_chars(paths: list[Path]) -> set[str]:
    chars: set[str] = set()
    for path in paths:
        raw = path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            chars.update(raw)
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, str):
                chars.update(node)
            elif isinstance(node, dict):
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return chars


def is_han(ch: str) -> bool:
    cp = ord(ch)
    return 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF


# 与两份 PDF 生成器 _fix_dot() 保持一致的归一化规则：
#   1) 拉丁扩展字母走 NFKD 降级（ç→c、É→E、š→s），连字展开（ß→ss、ø→o）；
#   2) 上下标转写为 ASCII 科学记法（²³→^23、⁻→^-）；
#   3) 中点 / 偏导 / 生僻元素符号走符号映射表。
# 这些字符在生成器里已被处理，渲染成 ASCII 后是安全的，不应被报为缺陷。
_SPECIAL_LATIN = {
    "ß": "ss", "Æ": "AE", "æ": "ae", "Œ": "OE", "œ": "oe",
    "Ø": "O", "ø": "o", "Ł": "L", "ł": "l", "Ð": "D", "ð": "d", "Þ": "Th", "þ": "th",
    "đ": "d", "Đ": "D", "ħ": "h", "Ħ": "H", "ı": "i", "İ": "I",
    "ŋ": "n", "Ŋ": "N", "ŧ": "t", "Ŧ": "T",
}
_SUPER_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-")
_SUB_MAP = str.maketrans("₀₁₂₃₄₅₆₇₈₉₊₋", "0123456789+-")
_SPECIAL_SYMBOLS = {"·": "\u30fb", "\u30fb": "\u30fb", "‧": "\u30fb", "∂": "partial", "𬭳": "Sg"}
# 上下标整体转写为 ASCII 科学记法（²³ → ^23），整体仍是纯 ASCII 即可视为安全
_SUPER_CHARS = "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻"
_SUB_CHARS = "₀₁₂₃₄₅₆₇₈₉₊₋"


def normalize_like_generator(text: str) -> str:
    """按生成器 _fix_dot() 的规则归一化，返回归一化后的字符串。"""
    out = []
    for ch in text:
        if ord(ch) < 128:
            out.append(ch)
        elif ch in _SPECIAL_SYMBOLS:
            out.append(_SPECIAL_SYMBOLS[ch])
        elif ch in _SPECIAL_LATIN:
            out.append(_SPECIAL_LATIN[ch])
        elif ch in _SUPER_CHARS or ch in _SUB_CHARS:
            out.append(ch.translate(_SUPER_MAP if ch in _SUPER_CHARS else _SUB_MAP))
        elif unicodedata.category(ch).startswith("L") and "LATIN" in unicodedata.name(ch, ""):
            decomposed = unicodedata.normalize("NFKD", ch)
            ascii_base = "".join(c for c in decomposed if ord(c) < 128)
            out.append(ascii_base or ch)
        else:
            out.append(ch)
    return "".join(out)


def render_probe(chars: list[str]) -> dict[str, str]:
    """把每个字符渲染进 PDF 后抽回，得到 {字符: 实际渲染结果}。"""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen import canvas

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(600, 800))
    c.setFont("STSong-Light", 12)
    per_page = 40
    for i, ch in enumerate(chars):
        if i > 0 and i % per_page == 0:
            c.showPage()
            c.setFont("STSong-Light", 12)
        c.drawString(20, 780 - (i % per_page) * 18, f"X{i:04d}[{ch}]Y")
    c.save()

    try:
        import pymupdf as fitz
    except ImportError:
        import fitz  # type: ignore

    with fitz.open(stream=buf.getvalue(), filetype="pdf") as doc:
        extracted = "\n".join(page.get_text() for page in doc)

    result: dict[str, str] = {}
    for i, ch in enumerate(chars):
        marker = f"X{i:04d}["
        start = extracted.find(marker)
        end = extracted.find("]Y", start) if start != -1 else -1
        if start == -1 or end == -1:
            result[ch] = ""
        else:
            result[ch] = extracted[start + len(marker):end]
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="检查数据集中会被 PDF CID 字体静默丢弃的字符")
    ap.add_argument("files", nargs="+", help="要检查的数据 JSON 路径")
    ap.add_argument(
        "--allow",
        default="",
        help="已在生成器 _fix_dot() 中转写处理、可安全忽略的字符（直接给出字符即可）",
    )
    ap.add_argument(
        "--apply-mapping",
        default="",
        help="额外忽略的码位集合（形如 'U+00B2,U+2202'），用于声明已由映射表覆盖的字符",
    )
    args = ap.parse_args()

    paths = []
    for raw in args.files:
        p = Path(raw)
        if not p.is_absolute():
            p = ROOT / raw
        if not p.exists():
            print(f"✗ 找不到文件：{p}", file=sys.stderr)
            return 1
        paths.append(p)

    allowed = set(args.allow)
    mapped = set()
    for token in args.apply_mapping.split(","):
        token = token.strip()
        if not token:
            continue
        if token.upper().startswith("U+"):
            mapped.add(chr(int(token[2:], 16)))
        else:
            mapped.add(token)

    all_chars = collect_chars(paths)
    # 先按生成器规则归一化：被映射覆盖的字符（拉丁重音/上下标/中点等）直接判定为安全
    normalized = {ch: normalize_like_generator(ch) for ch in all_chars}
    safe = {
        ch for ch, norm in normalized.items()
        if norm != ch and all(ord(c) < 128 or c in "\u30fb" for c in norm)
    }
    suspects = sorted(
        ch for ch in all_chars
        if ord(ch) >= 128 and not is_han(ch) and ch not in allowed and ch not in mapped and ch not in safe
    )

    if not suspects:
        print(
            f"✓ 全部 {len(all_chars)} 个字符均已安全处理"
            f"（{len(safe)} 个经生成器归一化，{len(all_chars) - len(safe)} 个为 ASCII/汉字）"
        )
        return 0

    rendered = render_probe(suspects)
    broken = []
    for ch in suspects:
        got = rendered.get(ch, "")
        if got != ch:
            broken.append((ch, got))

    if not broken:
        print(f"✓ {len(suspects)} 个非 ASCII 非汉字字符均可被 STSong-Light 正确渲染")
        return 0

    print(f"✗ 以下 {len(broken)} 个字符会被 STSong-Light 静默丢弃或破坏：\n")
    for ch, got in broken:
        name = unicodedata.name(ch, "UNKNOWN")
        shown = "（整段被截断）" if got == "" else f"渲染成 {got!r}"
        print(f"  U+{ord(ch):04X}  {ch!r}  {name}  →  {shown}")
    print("\n处理方式：在两份 PDF 生成器的 _fix_dot() 里补映射（NFKD 降级 / 上下标转写 / 符号替换），")
    print("或用 --allow / --apply-mapping 声明这些字符已被覆盖。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
