#!/usr/bin/env python3
"""主题日历「月度缩览版」PDF 生成器（一人一行：日期 + 名字 + 名言）。

用法：
  python generate_monthly_pdf.py --config theme.json [--out output/pdf/月度版.pdf]

版面：纵向 A4 + 三栏 best-fit 流式排版；某月条目过多时自动续页（页眉标注「续」）。
本文件已内建本项目踩过的坑（见 SKILL.md），改字段映射即可换主题，不必改代码。
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

W, H = A4  # 纵向 595.28 × 841.89
MONTH_CN = ["", "一月", "二月", "三月", "四月", "五月", "六月",
            "七月", "八月", "九月", "十月", "十一月", "十二月"]

INK = HexColor("#15263D")
PAPER = HexColor("#F7F1E7")
MUTED = HexColor("#6F7580")
LINE = HexColor("#D6CDBD")
ACCENTS = {
    "blue": HexColor("#C9DAE7"), "coral": HexColor("#F1B8A7"),
    "gold": HexColor("#F0D88D"), "green": HexColor("#BED8B6"),
    "violet": HexColor("#C9BEE1"),
}

MARGIN, COL_GAP, N_COLS = 40, 16, 3
CONTENT_TOP = H - 96
CONTENT_BOTTOM = 44
HEADER_LINE = H - 90
NAME_SIZE, DAY_SIZE, QUOTE_SIZE, QUOTE_LEAD = 11, 13, 8, 11
DAY_NAME_BASE = 13      # 日期/名字基线 = y_top - 13
QUOTE_BASE_GAP = 13      # 名言首行基线 = y_top - 26（与日期行留净空，防压字）
BOTTOM_GAP = 7


def font(name: str = "cn") -> str:
    return "STSong-Light" if name == "cn" else "Helvetica"


def draw_text(c, text, x, y, size, color=INK, face="cn"):
    c.setFillColor(color)
    c.setFont(font(face), size)
    c.drawString(x, y, text)


def wrap_lines(c, text, width, size, face="cn", cap=None):
    c.setFont(font(face), size)
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
    """把配置里的字段映射封装成取值器，主题换了只改 JSON。"""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.fm = cfg["fieldMap"]
        self.unit = cfg.get("theme", {}).get("unitLabel", "位人物")

    def get(self, entry: dict, role: str, default="") -> str:
        key = self.fm.get(role)
        if not key:
            return default
        return str(entry.get(key, default) or default)

    def quote_of(self, entry: dict, quotes: dict) -> str:
        q = quotes.get(self.get(entry, "id"))
        if isinstance(q, dict) and q.get("text"):
            return q["text"]
        if isinstance(q, str) and q.strip():
            return q
        return self.get(entry, "tagline", "—")


def block_height(c, entry, theme, quotes, col_w):
    """区块高度 —— 排版(pack)与绘制(draw)必须共用这一个函数。

    坑：曾经排版用一套高度、绘制用另一套(高 12pt)，导致最忙月份的末条被挤出页底。
    """
    lines = wrap_lines(c, theme.quote_of(entry, quotes), col_w - 12, QUOTE_SIZE, cap=2)
    n = len(lines)
    ink_top = 3
    ink_bottom = 26 + (n - 1) * QUOTE_LEAD + 2
    return (ink_bottom - ink_top) + BOTTOM_GAP, lines


def pack_month(c, entries, theme, quotes, col_w):
    """best-fit 平衡分栏，超限续页。返回 [( [col0..colN], [col_x...] ), ...]"""
    col_x = [MARGIN + i * (col_w + COL_GAP) for i in range(N_COLS)]
    pages, cols = [], [[] for _ in range(N_COLS)]
    col_y = [CONTENT_TOP] * N_COLS
    for entry in entries:
        h, _ = block_height(c, entry, theme, quotes, col_w)
        ci = max(range(N_COLS), key=lambda i: col_y[i])
        if col_y[ci] - h < CONTENT_BOTTOM:
            pages.append((cols, col_x[:]))
            cols = [[] for _ in range(N_COLS)]
            col_y = [CONTENT_TOP] * N_COLS
            ci = max(range(N_COLS), key=lambda i: col_y[i])
        cols[ci].append(entry)
        col_y[ci] -= h
    if any(cols):
        pages.append((cols, col_x[:]))
    return pages


def draw_header(c, month, count, theme, continuation=False):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    accent = list(ACCENTS.values())[(month - 1) % len(ACCENTS)]
    c.setFillColor(accent)
    c.rect(0, H - 14, W, 14, fill=1, stroke=0)
    draw_text(c, f"{month:02d}", MARGIN, H - 62, 46, INK, "latin")
    draw_text(c, MONTH_CN[month], MARGIN + 58, H - 58, 30, INK)
    sub = f"{count} {theme.unit}的生日在这个月" + (" · 续" if continuation else "")
    draw_text(c, sub, MARGIN + 60, H - 76, 10, MUTED)
    # 坑：标题含中文，必须用中文字体。用 Helvetica(latin) 会把汉字渲成豆腐块(III…)。
    title = theme.cfg.get("theme", {}).get("name", "主题日历")
    draw_text(c, f"{title} · 月度版", W - MARGIN, H - 76, 8, MUTED)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(MARGIN, HEADER_LINE, W - MARGIN, HEADER_LINE)


def draw_block(c, entry, x, y_top, col_w, theme, quotes):
    accent = ACCENTS.get(entry.get("color", "blue"), ACCENTS["blue"])
    day = f"{int(entry[theme.fm['day']]):02d}"
    name = theme.get(entry, "name")

    # 坑：超长名字会越出本栏、压到邻栏文字。必须按栏宽缩字号，仍放不下就截断。
    day_w = c.stringWidth(day, font("latin"), DAY_SIZE)
    gap = 6
    avail = col_w - day_w - gap - 4
    size, shown = NAME_SIZE, name
    c.setFont(font("cn"), size)
    while size >= 7:
        if c.stringWidth(name, font("cn"), size) <= avail:
            break
        size -= 1
    else:
        cur = ""
        for ch in name:
            if c.stringWidth(cur + ch + "…", font("cn"), 7) > avail:
                break
            cur += ch
        shown, size = cur + "…", 7

    draw_text(c, day, x, y_top - DAY_NAME_BASE, DAY_SIZE, accent, "latin")
    draw_text(c, shown, x + day_w + gap, y_top - DAY_NAME_BASE, size, INK)
    lines = wrap_lines(c, theme.quote_of(entry, quotes), col_w - 12, QUOTE_SIZE, cap=2)
    qy = y_top - DAY_NAME_BASE - QUOTE_BASE_GAP
    for i, line in enumerate(lines):
        draw_text(c, line, x, qy - i * QUOTE_LEAD, QUOTE_SIZE, MUTED)


def draw_footer(c, page_no, total):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(MARGIN, 30, W - MARGIN, 30)
    draw_text(c, f"第 {page_no:02d} 页 / 共 {total:02d} 页", MARGIN, 18, 8, MUTED)
    draw_text(c, "每天认识一位", W - MARGIN, 18, 8, MUTED)


def draw_cover(c, theme):
    c.setFillColor(INK)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor("#F0D88D"))
    c.circle(W / 2, 250, 60, fill=1, stroke=0)
    t = theme.cfg.get("theme", {})
    draw_text(c, t.get("name", "主题日历"), 70, 470, 38, HexColor("#F7F1E7"))
    draw_text(c, "月度生日版", 70, 422, 24, HexColor("#F0D88D"))
    draw_text(c, f"每个月，认识在这个月出生的{t.get('unitLabel','人物')}们——", 70, 372, 12, HexColor("#B6C0CC"))
    draw_text(c, "以及他们留下的那句话。", 70, 352, 12, HexColor("#B6C0CC"))
    draw_text(c, "生日 · 名字 · 名言", 70, 318, 13, HexColor("#F0B29F"))
    draw_text(c, f"PRINT EDITION · {datetime.date.today().year}", W - 160, 40, 8, HexColor("#B6C0CC"), "latin")
    c.showPage()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="主题配置 JSON")
    ap.add_argument("--out", default=None, help="输出 PDF 路径")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    theme = Theme(cfg)
    entries = json.loads(Path(cfg["entryFile"]).read_text(encoding="utf-8"))
    quotes = json.loads(Path(cfg["quoteFile"]).read_text(encoding="utf-8")) if cfg.get("quoteFile") else {}
    entries.sort(key=lambda e: (int(e[theme.fm["month"]]), int(e[theme.fm["day"]]), theme.get(e, "name")))

    by_month = {m: [] for m in range(1, 13)}
    for e in entries:
        by_month[int(e[theme.fm["month"]])].append(e)

    out = Path(args.out or Path(cfg.get("outputDir", "output/pdf")) / f"{cfg['theme'].get('name','主题日历')}_月度生日版_A4.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    c = canvas.Canvas(str(out), pagesize=(W, H), pageCompression=1)
    c.setTitle(f"{cfg['theme'].get('name','主题日历')} - 月度生日版")
    draw_cover(c, theme)

    col_w = (W - 2 * MARGIN - (N_COLS - 1) * COL_GAP) / N_COLS
    schedule = [(m, pack_month(c, by_month[m], theme, quotes, col_w)) for m in range(1, 13)]
    total_pages = 1 + sum(len(p) for _, p in schedule)

    page_no = 0
    for month, pages in schedule:
        for pi, (cols, col_x) in enumerate(pages):
            page_no += 1
            draw_header(c, month, len(by_month[month]), theme, continuation=pi > 0)
            for ci, col_entries in enumerate(cols):
                y = CONTENT_TOP
                for entry in col_entries:
                    h, _ = block_height(c, entry, theme, quotes, col_w)
                    draw_block(c, entry, col_x[ci], y, col_w, theme, quotes)
                    y -= h
            draw_footer(c, page_no, total_pages)
            c.showPage()
    c.save()
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
