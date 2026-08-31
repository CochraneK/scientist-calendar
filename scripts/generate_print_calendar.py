from __future__ import annotations

import datetime
import json
from pathlib import Path

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "app" / "scientists.json"
QUOTES = ROOT / "app" / "quotes.json"
OUTPUT_DIR = ROOT / "output" / "pdf"
# 版次年份随生成时间走，避免每年都要手改硬编码。
EDITION_YEAR = datetime.date.today().year
W, H = landscape(A4)

INK = HexColor("#15263D")
PAPER = HexColor("#F7F1E7")
CREAM = HexColor("#FFFDF8")
MUTED = HexColor("#6F7580")
LINE = HexColor("#D6CDBD")
ACCENTS = {
    "blue": HexColor("#C9DAE7"),
    "coral": HexColor("#F1B8A7"),
    "gold": HexColor("#F0D88D"),
    "green": HexColor("#BED8B6"),
    "violet": HexColor("#C9BEE1"),
}


def load_scientists() -> list[dict[str, str]]:
    records = json.loads(DATA.read_text(encoding="utf-8"))
    if not records:
        raise RuntimeError("No calendar records found")
    return sorted(records, key=lambda item: (int(item["month"]), int(item["day"]), item["name"]))


def output_path(count: int) -> Path:
    return OUTPUT_DIR / f"科学家日历_精选{count}位_A4打印版.pdf"


def load_quotes() -> dict[str, dict[str, str]]:
    return json.loads(QUOTES.read_text(encoding="utf-8"))


def font(name: str = "cn") -> str:
    return "STSong-Light" if name == "cn" else "Helvetica"


def draw_text(c: canvas.Canvas, text: str, x: float, y: float, size: float, color=INK, face="cn") -> None:
    c.setFillColor(color)
    c.setFont(font(face), size)
    c.drawString(x, y, text)


def draw_centered(c: canvas.Canvas, text: str, x: float, y: float, size: float, color=INK, face="cn") -> None:
    c.setFillColor(color)
    c.setFont(font(face), size)
    c.drawCentredString(x, y, text)


def wrap_lines(c: canvas.Canvas, text: str, width: float, size: float, face="cn") -> list[str]:
    c.setFont(font(face), size)
    lines, current = [], ""
    for char in text:
        if c.stringWidth(current + char, font(face), size) <= width:
            current += char
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: float, size: float, leading: float, color=INK) -> float:
    lines = wrap_lines(c, text, width, size)
    c.setFillColor(color)
    c.setFont(font(), size)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def draw_mark(c: canvas.Canvas, x: float, y: float, size: float = 18) -> None:
    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    c.circle(x, y, size / 2, stroke=1, fill=0)
    c.setFillColor(INK)
    dot = size / 10
    c.circle(x - size / 5, y + size / 9, dot, stroke=0, fill=1)
    c.circle(x + size / 5, y + size / 9, dot, stroke=0, fill=1)
    c.circle(x, y - size / 5, dot, stroke=0, fill=1)


def draw_cover(c: canvas.Canvas, count: int) -> None:
    image = ROOT / "public" / "og.jpg"
    c.setFillColor(INK)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    if image.exists():
        image_width = H * 1664 / 936
        c.drawImage(ImageReader(str(image)), 0, 0, image_width, H, preserveAspectRatio=False)
        c.setFillColor(Color(0.05, 0.11, 0.18, alpha=0.24))
        c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(Color(0.03, 0.08, 0.14, alpha=0.72))
    c.roundRect(42, 37, 400, 91, 7, fill=1, stroke=0)
    c.setFillColor(HexColor("#F0B29F"))
    c.setFont(font(), 19)
    c.drawString(61, 93, f"精选 {count} 位人物 · A4 横版打印样稿")
    c.setStrokeColor(HexColor("#DAB76A"))
    c.line(61, 75, 310, 75)
    c.setFillColor(Color(1, 1, 1, alpha=0.72))
    c.setFont(font(), 12)
    c.drawString(61, 54, "每天认识一位科学家，一项发现，与一个改变世界的念头。")
    c.setFillColor(Color(1, 1, 1, alpha=0.64))
    c.setFont("Helvetica", 9)
    c.drawRightString(W - 45, 34, f"PRINT EDITION · {EDITION_YEAR}")
    c.showPage()


def draw_overview(c: canvas.Canvas, entries: list[dict[str, str]]) -> None:
    grouped = {month: [] for month in range(1, 13)}
    for entry in entries:
        grouped[int(entry["month"])].append(entry)

    # Two pages, 6 months each; each month box wraps entries into N columns.
    for page_start in (1, 7):
        c.setFillColor(PAPER)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        draw_mark(c, 47, H - 47)
        draw_text(c, "全年科学纪念日总览", 75, H - 53, 26)
        draw_text(c, f"{len(entries)} SCIENCE NOTES · {page_start}-{page_start + 5} 月", 76, H - 72, 8, MUTED, "latin")

        col_w = (W - 84) / 3
        box_w = col_w - 17
        top = H - 128
        bottom = 46
        row_h = (top - bottom) / 2
        header_h = 38          # clear space below the month title line
        list_h = row_h - header_h - 4
        item_h = 15
        per_col = max(1, int(list_h // item_h))

        for offset in range(6):
            month = page_start + offset
            index = offset
            col, row = index % 3, index // 3
            x = 42 + col * col_w
            y_top = top - row * row_h
            c.setStrokeColor(LINE)
            c.setLineWidth(0.6)
            c.line(x, y_top, x + box_w, y_top)
            draw_text(c, f"{month:02d}", x, y_top - 22, 17, INK, "latin")
            draw_text(c, "月", x + 27, y_top - 20, 11, MUTED)
            entries_m = grouped[month]
            count = len(entries_m)
            # "N 人" drawn at far right of header, above the item area
            draw_text(c, f"{count} 人", x + box_w - 40, y_top - 20, 9, MUTED)

            # reserve a right margin so the count label never collides
            ncol = max(1, (count + per_col - 1) // per_col)
            inner_col_w = (box_w - 8) / ncol
            for i, entry in enumerate(entries_m):
                cc = i // per_col
                rr = i % per_col
                ex = x + 4 + cc * inner_col_w
                ey = y_top - header_h - rr * item_h
                accent = ACCENTS.get(entry["color"], ACCENTS["blue"])
                c.setFillColor(accent)
                c.circle(ex, ey + 3, 2.5, fill=1, stroke=0)
                draw_text(c, f"{int(entry['day']):02d}", ex + 6, ey, 7, MUTED, "latin")
                name = entry["name"][:5] if len(entry["name"]) > 6 else entry["name"]
                draw_text(c, name, ex + 17, ey, 6)

        draw_text(c, "带色点的日期收录了科学人物或科学史纪念。", 42, 29, 9, MUTED)
        draw_text(c, f"科学家日历 · {len(entries)} 个好奇心的起点", W - 230, 29, 9, MUTED)
        c.showPage()




def draw_print_notes(c: canvas.Canvas, count: int) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    draw_mark(c, 48, H - 49)
    draw_text(c, "版权与印刷说明", 76, H - 54, 27)
    draw_text(c, "PRINTING NOTES · FIRST EDITION", 76, H - 74, 8, MUTED, "latin")

    blocks = [
        ("建议规格", "A4 横向，100% 实际大小。单页打印可直接作为展示卡；双面装订建议选择短边翻转。"),
        ("纸张建议", "日常打印可用 100-120g 书写纸；做成桌面卡或礼品册时，建议使用 160-200g 哑光卡纸。"),
        ("装订与裁切", "保留页面白边用于装订或裁切。若采用活页夹，可在左侧预留打孔边；不建议勾选“适合页面”。"),
        ("内容说明", f"本册收录精选 {count} 位科学人物与科学纪念日，作为内容样稿。正式印刷前，请逐条完成日期、事实、图片与来源复核。"),
    ]
    y = H - 135
    for index, (title, text) in enumerate(blocks, start=1):
        c.setFillColor(ACCENTS[("coral", "blue", "green", "gold")[index - 1]])
        c.circle(67, y + 10, 16, fill=1, stroke=0)
        draw_centered(c, f"{index:02d}", 67, y + 6, 9, INK, "latin")
        draw_text(c, title, 103, y + 10, 16)
        y = draw_wrapped(c, text, 103, y - 16, 610, 11, 18, MUTED) - 26
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(103, y + 9, W - 58, y + 9)
        y -= 18

    c.setFillColor(INK)
    c.roundRect(57, 52, W - 114, 52, 6, fill=1, stroke=0)
    draw_text(c, f"科学家日历 · 精选 {count} 位人物 · {EDITION_YEAR} 版", 77, 81, 12, white)
    draw_text(c, "网页与可下载版本将持续补充完整的资料来源与印刷资源。", 77, 62, 9, HexColor("#B6C0CC"))
    c.showPage()


def draw_back_cover(c: canvas.Canvas) -> None:
    c.setFillColor(INK)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setStrokeColor(HexColor("#B48C46"))
    c.setLineWidth(0.7)
    for radius in (65, 125, 190, 265):
        c.circle(W - 128, H / 2, radius, stroke=1, fill=0)
    c.setFillColor(HexColor("#F0D88D"))
    c.circle(W - 128, H / 2, 8, fill=1, stroke=0)
    draw_text(c, "把今天的好奇", 70, 325, 33, white)
    draw_text(c, "留给明天的问题。", 70, 276, 33, white)
    c.setStrokeColor(HexColor("#DAB76A"))
    c.line(70, 236, 313, 236)
    draw_text(c, "科学家日历", 70, 195, 18, HexColor("#F0D88D"))
    draw_text(c, "每天认识一位科学家", 70, 170, 11, HexColor("#B6C0CC"))
    draw_text(c, "cochranek.github.io/scientist-calendar", 70, 72, 10, HexColor("#B6C0CC"), "latin")
    draw_text(c, f"PRINT EDITION · {EDITION_YEAR}", W - 190, 42, 8, HexColor("#B6C0CC"), "latin")
    c.showPage()


def draw_entry(c: canvas.Canvas, entry: dict[str, str], page: int, total: int, quotes: dict[str, dict[str, str]]) -> None:
    accent = ACCENTS.get(entry["color"], ACCENTS["blue"])
    c.setFillColor(CREAM)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(INK)
    c.rect(0, H - 115, W, 115, fill=1, stroke=0)
    c.setFillColor(accent)
    c.circle(W - 89, H - 55, 32, fill=1, stroke=0)
    draw_mark(c, 42, H - 45)
    draw_text(c, "科学家日历", 65, H - 48, 17, white)
    draw_text(c, "DAILY SCIENCE NOTEBOOK", 65, H - 67, 7, HexColor("#B6C0CC"), "latin")
    draw_text(c, f"{int(entry['month']):02d}.{int(entry['day']):02d}", W - 176, H - 58, 21, INK, "latin")

    # Monogram circle (ink-saving print default)
    cx, cy, r = 132, 290, 87
    c.setFillColor(accent)
    c.circle(cx, cy, r, fill=1, stroke=0)
    draw_centered(c, entry["name"][0], cx, cy - 32, 95)
    c.setStrokeColor(INK)
    c.setLineWidth(0.85)
    c.circle(cx, cy, r, fill=0, stroke=1)
    draw_centered(c, entry["field"], cx, cy - 104, 10, INK)
    c.setStrokeColor(LINE)
    c.line(45, 151, 219, 151)
    draw_centered(c, entry["relation"], cx, cy - 157, 9, MUTED)

    left = 273
    draw_text(c, entry["relation"] + " · " + entry["years"], left, 430, 10, MUTED)
    name_len = len(entry["name"])
    name_size = 40 if name_len <= 5 else (34 if name_len <= 7 else (28 if name_len <= 9 else (23 if name_len <= 11 else 19)))
    draw_text(c, entry["name"], left, 383, name_size)
    draw_text(c, entry["latinName"] + " · " + entry["country"], left, 358, 10, MUTED)
    # ---------- 布局：固定卡片 + 受约束的引语/故事，全部在卡片顶(224)之上 ----------
    # 卡片为固定矩形：底 224，顶 64，高 160。卡片圆角填充会覆盖其内部任何矢量，
    # 因此上方的引语/故事/分隔线/来源的基线都必须 >= CONTENT_FLOOR(230)，
    # 才能保证字形下沿 (size 12 下沿 227.6) 仍高于卡片顶 224，不会被遮。
    CARD_BOTTOM = 224
    CARD_TOP = 64
    BOX_H = CARD_BOTTOM - CARD_TOP  # 160
    CONTENT_FLOOR = 230              # 卡片顶 + 6px 安全

    contrib_w, fact_w = 205, 238
    pad_top, pad_bottom, label_gap = 16, 10, 22
    room = BOX_H - pad_top - pad_bottom - label_gap  # 134

    def fit_lines(text: str, width: float, size: float, leading: float) -> list[str]:
        lines = wrap_lines(c, text or "—", width, size)
        max_lines = max(1, int(room // leading) + 1)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1][:max(1, len(lines[-1]) - 1)] + "…"
        return lines

    contrib_lines = fit_lines(entry["contribution"], contrib_w, 11, 15)
    fact_lines = fit_lines(entry["fact"], fact_w, 9, 13)
    box_h = BOX_H
    card_top = CARD_TOP

    # ---------- 引语：限制行数，使最后一行的基线 >= CONTENT_FLOOR ----------
    quotation = quotes.get(entry["id"])
    quote_text = quotation["text"] if quotation else entry.get("quote")
    quote_source = quotation["source"] if quotation else entry.get("quoteSource")
    has_sourced_quote = bool(quote_text and quote_source)
    quote_size = 18 if has_sourced_quote else 15
    quote_lead = 26 if has_sourced_quote else 23
    quote_color = HexColor("#B85E4C") if has_sourced_quote else MUTED
    quote_prefix = "“" if has_sourced_quote else "阅读线索｜"
    quote_suffix = "”" if has_sourced_quote else ""
    quote_full = quote_prefix + (quote_text or entry.get("tagline", "")) + quote_suffix
    # 末行基线 >= CONTENT_FLOOR => n <= (315 - CONTENT_FLOOR)/lead + 1
    max_q_lines = max(1, (315 - CONTENT_FLOOR) // quote_lead + 1)
    if has_sourced_quote:
        # 来源文字写在 quote_end 之下，强制 n<=3 以避免来源被推回与末行重叠
        max_q_lines = min(max_q_lines, 3)
    q_lines = wrap_lines(c, quote_full, 490, quote_size)
    if len(q_lines) > max_q_lines:
        q_lines = q_lines[:max_q_lines]
        q_lines[-1] = q_lines[-1][:max(1, len(q_lines[-1]) - 1)] + "…"
    quote_end = draw_wrapped(c, "".join(q_lines), left, 315, 490, quote_size, quote_lead, quote_color)
    if has_sourced_quote:
        src_y = max(quote_end - 5, CONTENT_FLOOR)
        draw_text(c, "— " + str(quote_source), left, src_y, 8, MUTED)
        divider_y = max(quote_end - 20, CONTENT_FLOOR + 5)
    else:
        divider_y = max(quote_end - 5, CONTENT_FLOOR + 5)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(left, divider_y, W - 48, divider_y)

    # ---------- 故事：在分隔线与 CONTENT_FLOOR 之间，最后一行基线 >= CONTENT_FLOOR ----------
    # 直接在固定 y 上逐行绘制（不再 join+rewrap），避免重新换行产生多余行穿入卡片
    story_top = max(divider_y - 30, CONTENT_FLOOR + 20)
    available = story_top - CONTENT_FLOOR
    max_story_lines = max(0, available // 20 + 1)
    if max_story_lines > 0:
        story_lines = wrap_lines(c, entry["story"], 490, 12)
        if len(story_lines) > max_story_lines:
            kept = story_lines[:max_story_lines - 1]
            src_line = story_lines[max_story_lines - 1]
            kept.append(src_line[:max(1, len(src_line) - 1)] + "…")
        else:
            kept = story_lines
        for idx, line in enumerate(kept):
            y_line = story_top - idx * 20
            if y_line < CONTENT_FLOOR:
                break
            draw_text(c, line, left, y_line, 12, INK)

    # ---------- 卡片（最后画，确保任何越界都被覆盖也不影响已画的卡片） ----------
    c.setFillColor(HexColor("#F0EBE1"))
    c.roundRect(left, card_top, 235, box_h, 5, fill=1, stroke=0)
    c.roundRect(left + 255, card_top, 265, box_h, 5, fill=1, stroke=0)
    # 卡片内文字：直接逐行绘制（不 join+rewrap），行高分别 15/13，底线不低于 card_top+pad_bottom
    draw_text(c, "核心贡献", left + 14, card_top + box_h - pad_top, 8, MUTED)
    draw_text(c, "你知道吗", left + 269, card_top + box_h - pad_top, 8, MUTED)
    contrib_start_y = card_top + box_h - pad_top - label_gap + 6
    for idx, line in enumerate(contrib_lines):
        y_line = contrib_start_y - idx * 15
        if y_line < card_top + pad_bottom:
            break
        draw_text(c, line, left + 14, y_line, 11, INK)
    fact_start_y = card_top + box_h - pad_top - label_gap + 7
    for idx, line in enumerate(fact_lines):
        y_line = fact_start_y - idx * 13
        if y_line < card_top + pad_bottom:
            break
        draw_text(c, line, left + 269, y_line, 9, INK)

    c.setStrokeColor(LINE)
    c.line(43, 42, W - 43, 42)
    draw_text(c, f"第 {page:02d} 页 / {total:02d}", 43, 25, 8, MUTED)
    draw_text(c, "每天认识一位科学家", W - 160, 25, 8, MUTED)
    c.showPage()


def main() -> None:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    entries = load_scientists()
    quotes = load_quotes()
    output = output_path(len(entries))
    output.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output), pagesize=(W, H), pageCompression=1)
    c.setTitle(f"科学家日历 - 精选{len(entries)}位 A4打印版")
    c.setAuthor("科学家日历")
    draw_cover(c, len(entries))
    draw_print_notes(c, len(entries))
    draw_overview(c, entries)
    # 封面 1 页 + 说明 1 页 + 总览 2 页 = 4 页，人物页从第 5 页开始。
    total = len(entries) + 4
    for number, entry in enumerate(entries, start=5):
        draw_entry(c, entry, number, total, quotes)
    draw_back_cover(c)
    c.save()
    print(output)


if __name__ == "__main__":
    main()
