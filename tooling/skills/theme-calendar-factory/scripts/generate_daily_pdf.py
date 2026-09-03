#!/usr/bin/env python3
"""主题日历「每日人物版」PDF 生成器（横版 A4，一人一页）。

用法：
  python generate_daily_pdf.py --config theme.json [--out output/pdf/每日版.pdf]

本文件把本项目踩过的坑全部内建为约束，改配置即可换主题：
  1. 卡片顶边固定、高度自适应（固定高框在短内容时非常丑）
  2. 引语→来源→分隔线→故事 严格自上而下流水布局，结构上不可能互压
  3. 故事/名言逐行绘制，绝不 join 后重新换行（重排会多出一行穿进卡片）
  4. roundRect 的"顶边"是 card_top + box_h，不是 card_top（y 轴向上）
  5. 卡片最后绘制（不透明填充会盖住其后内容）
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

W, H = landscape(A4)  # 横版 841.89 × 595.28
MONTH_CN = ["", "一月", "二月", "三月", "四月", "五月", "六月",
            "七月", "八月", "九月", "十月", "十一月", "十二月"]

INK = HexColor("#15263D")
PAPER = HexColor("#F7F1E7")
CREAM = HexColor("#FFFDF8")
MUTED = HexColor("#6F7580")
LINE = HexColor("#D6CDBD")
CARD_BG = HexColor("#F0EBE1")
ACCENTS = {
    "blue": HexColor("#C9DAE7"), "coral": HexColor("#F1B8A7"),
    "gold": HexColor("#F0D88D"), "green": HexColor("#BED8B6"),
    "violet": HexColor("#C9BEE1"),
}

# ---- 版面常量（与 verify 脚本的 --card-color 对应）----
CARD_TOP_EDGE = 224      # 卡片顶边(y-up)固定
MIN_BOX_H = 46
MAX_BOX_H = 174
CONTENT_FLOOR = 230      # 卡片顶 + 6px 安全：正文基线不得低于此值
Q_START = 333            # 引语起点（在姓名行 y=383 之下，不撞）
LEFT = 273               # 右栏左边界


def font(name: str = "cn") -> str:
    return "STSong-Light" if name == "cn" else "Helvetica"


# STSong-Light(Adobe-GB1 CID 字体)不含 U+00B7(MIDDLE DOT)字形，画到 · 会整段丢失；
# 数据里名姓/分隔常用 U+00B7，画中文(face="cn")时统一替换为 U+30FB(片假名中点，CID 可渲染)。
_CN_DOT = "\u30fb"


def _fix_dot(text, face):
    return text.replace("\u00b7", _CN_DOT) if face == "cn" else text


def draw_text(c, text, x, y, size, color=INK, face="cn"):
    c.setFillColor(color)
    c.setFont(font(face), size)
    c.drawString(x, y, _fix_dot(text, face))


def draw_centered(c, text, x, y, size, color=INK):
    c.setFillColor(color)
    c.setFont(font("cn"), size)
    c.drawCentredString(x, y, _fix_dot(text, "cn"))


def wrap_lines(c, text, width, size, face="cn", cap=None):
    c.setFont(font(face), size)
    text = _fix_dot(text, face)
    lines, cur = [], ""
    for ch in text:
        if c.stringWidth(cur + ch, font(face), size) <= width:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    if cap is not None and len(lines) > cap:
        lines = lines[:cap]
        lines[-1] = lines[-1][:max(1, len(lines[-1]) - 1)] + "…"
    return lines


class Theme:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.fm = cfg["fieldMap"]

    def get(self, entry: dict, role: str, default="") -> str:
        key = self.fm.get(role)
        return str(entry.get(key, default) or default) if key else default

    def quote(self, entry, quotes):
        q = quotes.get(self.get(entry, "id"))
        text = q.get("text") if isinstance(q, dict) else (q if isinstance(q, str) else None)
        source = q.get("source") if isinstance(q, dict) else None
        return text or "", source or ""


def draw_mark(c, x, y, size=18):
    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    c.circle(x, y, size / 2, stroke=1, fill=0)
    c.setFillColor(INK)
    dot = size / 10
    c.circle(x - size / 5, y + size / 9, dot, stroke=0, fill=1)
    c.circle(x + size / 5, y + size / 9, dot, stroke=0, fill=1)
    c.circle(x, y - size / 5, dot, stroke=0, fill=1)


def draw_entry(c, entry, theme, quotes, page, total):
    fm = theme.fm
    accent = ACCENTS.get(entry.get("color", "blue"), ACCENTS["blue"])
    c.setFillColor(CREAM)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(INK)
    c.rect(0, H - 115, W, 115, fill=1, stroke=0)
    c.setFillColor(accent)
    c.circle(W - 89, H - 55, 32, fill=1, stroke=0)
    draw_mark(c, 42, H - 45)
    title = theme.cfg.get("theme", {}).get("name", "主题日历")
    draw_text(c, title, 65, H - 48, 17, white)
    draw_text(c, "DAILY NOTEBOOK", 65, H - 67, 7, HexColor("#B6C0CC"), "latin")
    draw_text(c, f"{int(entry[fm['month']]):02d}.{int(entry[fm['day']]):02d}",
              W - 176, H - 58, 21, INK, "latin")

    # 左栏：字母/首字圆形标记
    cx, cy, r = 132, 290, 87
    c.setFillColor(accent)
    c.circle(cx, cy, r, fill=1, stroke=0)
    name = theme.get(entry, "name")
    draw_centered(c, name[0], cx, cy - 32, 95)
    c.setStrokeColor(INK)
    c.setLineWidth(0.85)
    c.circle(cx, cy, r, fill=0, stroke=1)
    draw_centered(c, theme.get(entry, "field"), cx, cy - 104, 10, INK)
    c.setStrokeColor(LINE)
    c.line(45, 151, 219, 151)
    draw_centered(c, theme.get(entry, "relation"), cx, cy - 157, 9, MUTED)

    left = LEFT
    draw_text(c, theme.get(entry, "relation") + " · " + theme.get(entry, "years"), left, 430, 10, MUTED)
    n = len(name)
    name_size = 40 if n <= 5 else (34 if n <= 7 else (28 if n <= 9 else (23 if n <= 11 else 19)))
    draw_text(c, name, left, 383, name_size)
    draw_text(c, theme.get(entry, "subtitle") + " · " + theme.get(entry, "place"), left, 358, 10, MUTED)

    # ---- 卡片：顶边固定 + 高度自适应（先算高度，最后才画）----
    contrib_w, fact_w = 205, 238
    pad_top, pad_bottom, label_gap = 16, 10, 22
    max_room = MAX_BOX_H - pad_top - pad_bottom - label_gap

    def fit(text, width, size, lead):
        lines = wrap_lines(c, text or "—", width, size)
        cap = max(1, int(max_room // lead) + 1)
        if len(lines) > cap:
            lines = lines[:cap]
            lines[-1] = lines[-1][:max(1, len(lines[-1]) - 1)] + "…"
        return lines

    card_a_label = theme.cfg.get("labels", {}).get("cardA", "核心贡献")
    card_b_label = theme.cfg.get("labels", {}).get("cardB", "你知道吗")
    contrib_lines = fit(theme.get(entry, "cardA"), contrib_w, 11, 15)
    fact_lines = fit(theme.get(entry, "cardB"), fact_w, 9, 13)
    content_h = pad_top + pad_bottom + label_gap + max(
        (len(contrib_lines) - 1) * 15, (len(fact_lines) - 1) * 13
    )
    box_h = max(MIN_BOX_H, min(MAX_BOX_H, content_h))
    card_top = CARD_TOP_EDGE - box_h  # 底边浮动 → 短内容矮卡片

    # ---- 引语 → 来源 → 分隔线 → 故事：严格自上而下，物理上不可能互压 ----
    FLOOR = CONTENT_FLOOR
    q_text, q_source = theme.quote(entry, quotes)
    has_src = bool(q_text and q_source)
    lead = 26 if has_src else 23
    q_size = 18 if has_src else 15
    q_color = HexColor("#B85E4C") if has_src else MUTED
    prefix = "“" if has_src else "阅读线索｜"
    suffix = "”" if has_src else ""
    full = prefix + (q_text or theme.get(entry, "tagline")) + suffix
    room = Q_START - FLOOR
    need = 26 if has_src else 0
    max_q = min(max(1, (room - need) // lead), 2 if has_src else 3)
    q_lines = wrap_lines(c, full, 490, q_size, cap=max_q)

    y = Q_START
    c.setFillColor(q_color)
    c.setFont(font("cn"), q_size)
    for line in q_lines:
        c.drawString(left, y, line)
        y -= lead
    if has_src:
        src_y = y - 6
        draw_text(c, "— " + q_source, left, src_y, 8, MUTED)
        divider_y = src_y - 12
    else:
        divider_y = y - 6
    divider_y = max(divider_y, FLOOR + 6)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(left, divider_y, W - 48, divider_y)

    # 故事：分隔线之下逐行绘制，底线不低于 FLOOR（绝不 re-wrap）
    story_top = max(divider_y - 30, FLOOR + 22)
    max_story = max(0, (story_top - FLOOR) // 20 + 1)
    if max_story > 0:
        lines = wrap_lines(c, theme.get(entry, "story"), 490, 12)
        if len(lines) > max_story:
            kept = lines[: max_story - 1]
            last = lines[max_story - 1]
            kept.append(last[:max(1, len(last) - 1)] + "…")
        else:
            kept = lines
        for i, line in enumerate(kept):
            y_line = story_top - i * 20
            if y_line < FLOOR:
                break
            draw_text(c, line, left, y_line, 12, INK)

    # ---- 卡片最后画：不透明填充覆盖其后内容 ----
    c.setFillColor(CARD_BG)
    c.roundRect(left, card_top, 235, box_h, 5, fill=1, stroke=0)
    c.roundRect(left + 255, card_top, 265, box_h, 5, fill=1, stroke=0)
    draw_text(c, card_a_label, left + 14, card_top + box_h - pad_top, 8, MUTED)
    draw_text(c, card_b_label, left + 269, card_top + box_h - pad_top, 8, MUTED)
    for i, line in enumerate(contrib_lines):
        y_line = card_top + box_h - pad_top - label_gap + 6 - i * 15
        if y_line < card_top + 4:
            break
        draw_text(c, line, left + 14, y_line, 11, INK)
    for i, line in enumerate(fact_lines):
        y_line = card_top + box_h - pad_top - label_gap + 7 - i * 13
        if y_line < card_top + 4:
            break
        draw_text(c, line, left + 269, y_line, 9, INK)

    c.setStrokeColor(LINE)
    c.line(43, 42, W - 43, 42)
    draw_text(c, f"第 {page:02d} 页 / {total:02d}", 43, 25, 8, MUTED)
    draw_text(c, "每天认识一位", W - 160, 25, 8, MUTED)
    c.showPage()


def draw_cover(c, theme, count):
    c.setFillColor(INK)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    t = theme.cfg.get("theme", {})
    draw_text(c, t.get("name", "主题日历"), 61, 300, 44, white)
    draw_text(c, f"精选 {count} {t.get('unitLabel','位人物')} · A4 横版打印版", 61, 240, 18, HexColor("#F0B29F"))
    draw_text(c, f"PRINT EDITION · {datetime.date.today().year}", W - 220, 40, 9, HexColor("#B6C0CC"), "latin")
    c.showPage()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    theme = Theme(cfg)
    entries = json.loads(Path(cfg["entryFile"]).read_text(encoding="utf-8"))
    quotes = json.loads(Path(cfg["quoteFile"]).read_text(encoding="utf-8")) if cfg.get("quoteFile") else {}
    entries.sort(key=lambda e: (int(e[theme.fm["month"]]), int(e[theme.fm["day"]]), theme.get(e, "name")))

    out = Path(args.out or Path(cfg.get("outputDir", "output/pdf")) / f"{cfg['theme'].get('name','主题日历')}_每日版_A4.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    c = canvas.Canvas(str(out), pagesize=(W, H), pageCompression=1)
    c.setTitle(f"{cfg['theme'].get('name','主题日历')} - 每日版")
    draw_cover(c, theme, len(entries))
    # +1 = 封底
    total = len(entries) + 1
    for i, entry in enumerate(entries, start=1):
        draw_entry(c, entry, theme, quotes, i, total)

    c.setFillColor(INK)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    draw_text(c, "把今天的好奇", 70, 325, 33, white)
    draw_text(c, "留给明天的问题。", 70, 276, 33, white)
    draw_text(c, cfg["theme"].get("name", "主题日历"), 70, 195, 18, HexColor("#F0D88D"))
    c.showPage()
    c.save()
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
