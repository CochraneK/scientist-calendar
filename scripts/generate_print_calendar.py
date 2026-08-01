from __future__ import annotations

import re
import json
from pathlib import Path

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "app" / "page.tsx"
QUOTES = ROOT / "app" / "quotes.json"
OUTPUT_DIR = ROOT / "output" / "pdf"
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
    source = SOURCE.read_text(encoding="utf-8")
    objects = re.findall(r'\{ id: "(?P<id>[^"]+)", (?P<body>.*?) \}(?:,|(?=\n\s*\]))', source, re.S)
    required = ("month", "day", "name", "latinName", "years", "field", "country", "color", "relation", "tagline", "story", "contribution", "fact")
    records: list[dict[str, str]] = []
    for item_id, body in objects:
        record = {"id": item_id}
        for key, value in re.findall(r'(\w+): "([^"]*)"', body):
            record[key] = value
        for key, value in re.findall(r'(month|day): (\d+)', body):
            record[key] = value
        if all(key in record for key in required):
            records.append(record)
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
    image = ROOT / "public" / "og.png"
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
    c.drawRightString(W - 45, 34, "PRINT EDITION · 2026")
    c.showPage()


def draw_overview(c: canvas.Canvas, entries: list[dict[str, str]]) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    draw_mark(c, 47, H - 47)
    draw_text(c, "全年科学纪念日总览", 75, H - 53, 26)
    draw_text(c, f"{len(entries)} SCIENCE NOTES", 76, H - 72, 8, MUTED, "latin")
    grouped = {month: [] for month in range(1, 13)}
    for entry in entries:
        grouped[int(entry["month"])].append(entry)
    col_w, row_h = (W - 84) / 3, 105
    for month in range(1, 13):
        index = month - 1
        col, row = index % 3, index // 3
        x, y = 42 + col * col_w, H - 128 - row * row_h
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(x, y, x + col_w - 17, y)
        draw_text(c, f"{month:02d}", x, y - 22, 17, INK, "latin")
        draw_text(c, "月", x + 27, y - 20, 11, MUTED)
        item_y = y - 43
        for entry in grouped[month]:
            accent = ACCENTS.get(entry["color"], ACCENTS["blue"])
            c.setFillColor(accent)
            c.circle(x + 4, item_y + 3, 3, fill=1, stroke=0)
            draw_text(c, f"{int(entry['day']):02d}", x + 14, item_y, 8, MUTED, "latin")
            draw_text(c, entry["name"], x + 37, item_y, 10)
            item_y -= 18
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
    draw_text(c, f"科学家日历 · 精选 {count} 位人物 · 2026 扩充版", 77, 81, 12, white)
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
    draw_text(c, "PRINT EDITION · 2026", W - 190, 42, 8, HexColor("#B6C0CC"), "latin")
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

    c.setFillColor(accent)
    c.circle(132, 290, 87, fill=1, stroke=0)
    c.setStrokeColor(INK)
    c.setLineWidth(0.85)
    c.circle(132, 290, 87, fill=1, stroke=1)
    draw_centered(c, entry["name"][0], 132, 258, 95)
    draw_centered(c, entry["field"], 132, 186, 10, INK)
    c.setStrokeColor(LINE)
    c.line(45, 151, 219, 151)
    draw_centered(c, entry["relation"], 132, 133, 9, MUTED)

    left = 273
    draw_text(c, entry["relation"] + " · " + entry["years"], left, 430, 10, MUTED)
    name_size = 40 if len(entry["name"]) <= 7 else 34
    draw_text(c, entry["name"], left, 383, name_size)
    draw_text(c, entry["latinName"] + " · " + entry["country"], left, 358, 10, MUTED)
    quotation = quotes.get(entry["id"])
    quote_text = quotation["text"] if quotation else entry["tagline"]
    quote_end = draw_wrapped(c, "“" + quote_text + "”", left, 315, 490, 18, 26, HexColor("#B85E4C"))
    divider_y = quote_end - 5
    if quotation:
        draw_text(c, "— " + quotation["source"], left, quote_end - 5, 8, MUTED)
        divider_y = quote_end - 20
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(left, divider_y, W - 48, divider_y)
    body_end = draw_wrapped(c, entry["story"], left, divider_y - 30, 490, 12, 20, INK)

    meta_y = min(body_end - 12, 190)
    c.setFillColor(HexColor("#F0EBE1"))
    c.roundRect(left, meta_y - 32, 235, 66, 5, fill=1, stroke=0)
    c.roundRect(left + 255, meta_y - 32, 265, 66, 5, fill=1, stroke=0)
    draw_text(c, "核心贡献", left + 14, meta_y + 14, 8, MUTED)
    draw_text(c, entry["contribution"], left + 14, meta_y - 7, 12)
    draw_text(c, "你知道吗", left + 269, meta_y + 14, 8, MUTED)
    draw_wrapped(c, entry["fact"], left + 269, meta_y - 6, 238, 9, 13, INK)

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
    total = len(entries) + 4
    for number, entry in enumerate(entries, start=4):
        draw_entry(c, entry, number, total, quotes)
    draw_back_cover(c)
    c.save()
    print(output)


if __name__ == "__main__":
    main()
