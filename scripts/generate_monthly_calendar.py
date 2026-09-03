"""生成《科学家日历 · 月度生日版》A4 PDF。

每一页 = 一个月；该月所有科学家只显示：生日(日)、名字、名言。
采用纵向 A4 + 三栏流式排版；某月人数超限时自动续页（页眉标注 续）。
与 generate_print_calendar.py 解耦，复用 reportlab 中文字体(STSong-Light)。
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "app" / "scientists.json"
QUOTES = ROOT / "app" / "quotes.json"
OUTPUT_DIR = ROOT / "output" / "pdf"
EDITION_YEAR = datetime.date.today().year

W, H = A4  # 纵向 A4 ≈ 595.28 × 841.89

INK = HexColor("#15263D")
PAPER = HexColor("#F7F1E7")
MUTED = HexColor("#6F7580")
LINE = HexColor("#D6CDBD")
CREAM = HexColor("#FFFDF8")
ACCENTS = {
    "blue": HexColor("#C9DAE7"),
    "coral": HexColor("#F1B8A7"),
    "gold": HexColor("#F0D88D"),
    "green": HexColor("#BED8B6"),
    "violet": HexColor("#C9BEE1"),
}
MONTH_CN = ["", "一月", "二月", "三月", "四月", "五月", "六月",
            "七月", "八月", "九月", "十月", "十一月", "十二月"]


def load_scientists() -> list[dict]:
    records = json.loads(DATA.read_text(encoding="utf-8"))
    return sorted(records, key=lambda it: (int(it["month"]), int(it["day"]), it["name"]))


def load_quotes() -> dict:
    return json.loads(QUOTES.read_text(encoding="utf-8"))


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
        if lines:
            lines[-1] = lines[-1][:max(1, len(lines[-1]) - 1)] + "…"
    return lines


def quote_of(entry, quotes) -> str:
    q = quotes.get(entry["id"])
    if q and q.get("text"):
        return q["text"]
    return entry.get("tagline", "—")


# ---------- 区块几何 ----------
MARGIN = 40
COL_GAP = 16
N_COLS = 3
CONTENT_TOP = H - 96          # 页眉分隔线之下
CONTENT_BOTTOM = 44
HEADER_LINE = H - 90
NAME_SIZE = 11
DAY_SIZE = 13
QUOTE_SIZE = 8
QUOTE_LEAD = 11
NAME_H = 14
BOTTOM_GAP = 7
DAY_NAME_BASE = 13      # day/名字基线 = y_top - 13
QUOTE_BASE_GAP = 13      # 引语首行基线 = y_top - 13 - 13 = y_top - 26（与日期行留 3pt 净空）


def block_quote_height(c, entry, quotes, col_w):
    q = quote_of(entry, quotes)
    lines = wrap_lines(c, q, col_w - 12, QUOTE_SIZE, cap=2)
    n = len(lines)
    # 与 draw_block 完全一致：名字基线 y_top-13、首引语基线 y_top-26、行距 11。
    # 墨迹上沿≈ y_top-3、下沿≈ y_top-(26+(n-1)*11+2)；高度 = 墨迹跨度 + 块间留白。
    ink_top = 3
    ink_bottom = 26 + (n - 1) * QUOTE_LEAD + 2
    h = (ink_bottom - ink_top) + BOTTOM_GAP
    return h, lines


def pack_month(c, entries, quotes, col_w):
    """把一个月的条目用 best-fit 平衡分配到 N_COLS 栏；超限则续页。
    返回 list[page]，每页 = [col0_entries, col1_entries, col2_entries]。
    """
    col_x = [MARGIN + i * (col_w + COL_GAP) for i in range(N_COLS)]
    pages = []
    cols = [[] for _ in range(N_COLS)]
    col_y = [CONTENT_TOP] * N_COLS
    for entry in entries:
        h, _ = block_quote_height(c, entry, quotes, col_w)
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


def draw_header(c, month, count, continuation=False):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    # 顶部装饰条
    accent = list(ACCENTS.values())[(month - 1) % len(ACCENTS)]
    c.setFillColor(accent)
    c.rect(0, H - 14, W, 14, fill=1, stroke=0)
    # 大字月份
    draw_text(c, f"{month:02d}", MARGIN, H - 62, 46, INK, "latin")
    draw_text(c, MONTH_CN[month], MARGIN + 58, H - 58, 30, INK)
    sub = f"{count} 位科学家的生日在这个月"
    if continuation:
        sub += " · 续"
    draw_text(c, sub, MARGIN + 60, H - 76, 10, MUTED)
    # 注意：这行含中文，必须用中文字体。用 Helvetica(latin) 会把汉字渲染成豆腐块(III…)。
    draw_text(c, f"科学家日历 · 月度生日版 · {EDITION_YEAR}", W - MARGIN, H - 76, 8, MUTED)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(MARGIN, HEADER_LINE, W - MARGIN, HEADER_LINE)


def draw_block(c, entry, x, y_top, col_w, quotes):
    accent = ACCENTS.get(entry["color"], ACCENTS["blue"])
    day = f"{int(entry['day']):02d}"
    name = entry["name"]
    # 名字与日期同排；超宽则缩小字号，仍放不下则截断，确保不越过栏右缘
    day_w = c.stringWidth(day, font("latin"), DAY_SIZE)
    gap = 6
    avail = col_w - day_w - gap - 4
    name_size = NAME_SIZE
    shown = name
    c.setFont(font("cn"), name_size)
    while name_size >= 7:
        if c.stringWidth(name, font("cn"), name_size) <= avail:
            break
        name_size -= 1
    else:
        # 连 7pt 都放不下：按可用宽度逐字截断
        cur = ""
        for ch in name:
            if c.stringWidth(cur + ch + "…", font("cn"), 7) > avail:
                break
            cur += ch
        shown = cur + "…"
        name_size = 7
    # 日期（强调色）
    draw_text(c, day, x, y_top - DAY_NAME_BASE, DAY_SIZE, accent, "latin")
    # 名字（墨色）
    draw_text(c, shown, x + day_w + gap, y_top - DAY_NAME_BASE, name_size, INK)
    # 名言（与日期行留净空，避免压字）
    q = quote_of(entry, quotes)
    qlines = wrap_lines(c, q, col_w - 12, QUOTE_SIZE, cap=2)
    qy = y_top - DAY_NAME_BASE - QUOTE_BASE_GAP
    for i, line in enumerate(qlines):
        draw_text(c, line, x, qy - i * QUOTE_LEAD, QUOTE_SIZE, MUTED)


def draw_footer(c, page_no, total):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(MARGIN, 30, W - MARGIN, 30)
    draw_text(c, f"第 {page_no:02d} 页 / 共 {total:02d} 页", MARGIN, 18, 8, MUTED)
    draw_text(c, "每天认识一位科学家", W - MARGIN, 18, 8, MUTED)


def draw_cover(c):
    c.setFillColor(INK)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor("#F0D88D"))
    c.circle(W / 2, 250, 60, fill=1, stroke=0)
    draw_text(c, "科学家日历", 70, 470, 38, HexColor("#F7F1E7"))
    draw_text(c, "月度生日版", 70, 422, 24, HexColor("#F0D88D"))
    draw_text(c, "每个月，认识在这个月出生的科学家们——", 70, 372, 12, HexColor("#B6C0CC"))
    draw_text(c, "以及他们留下的那句话。", 70, 352, 12, HexColor("#B6C0CC"))
    draw_text(c, "生日 · 名字 · 名言", 70, 318, 13, HexColor("#F0B29F"))
    draw_text(c, f"PRINT EDITION · {EDITION_YEAR}", W - 160, 40, 8, HexColor("#B6C0CC"), "latin")
    c.showPage()


def main():
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    entries = load_scientists()
    quotes = load_quotes()
    by_month = {m: [] for m in range(1, 13)}
    for e in entries:
        by_month[int(e["month"])].append(e)

    output = OUTPUT_DIR / "科学家日历_月度生日版_A4.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output), pagesize=(W, H), pageCompression=1)
    c.setTitle("科学家日历 - 月度生日版 A4")
    c.setAuthor("科学家日历")

    draw_cover(c)

    # 先模拟排版，得到每张物理页的内容，便于计算总页码
    col_w = (W - 2 * MARGIN - (N_COLS - 1) * COL_GAP) / N_COLS
    schedule = []  # (month, continuation_index, pages_for_month)
    for month in range(1, 13):
        em = by_month[month]
        pages = pack_month(c, em, quotes, col_w)
        schedule.append((month, pages))

    total_pages = 1 + sum(len(pages) for _, pages in schedule)
    page_no = 0

    for month, pages in schedule:
        for pi, (cols, col_x) in enumerate(pages):
            page_no += 1
            cont = pi > 0
            draw_header(c, month, len(by_month[month]), continuation=cont)
            for ci, col_entries in enumerate(cols):
                x = col_x[ci]
                y = CONTENT_TOP
                for entry in col_entries:
                    h = block_quote_height(c, entry, quotes, col_w)[0]
                    draw_block(c, entry, x, y, col_w, quotes)
                    y -= h
            draw_footer(c, page_no, total_pages)
            c.showPage()

    c.save()
    print(output)


if __name__ == "__main__":
    main()
