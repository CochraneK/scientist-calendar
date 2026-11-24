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
import re
import sys
import unicodedata
from pathlib import Path

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
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
CARD_BOTTOM = 54         # 卡片底边固定在页脚分割线(y=42)之上 12pt，避免短卡片下方出现大面积空洞
MIN_BOX_H = 46
MAX_BOX_H = 160
Q_START = 333            # 引语起点（在姓名行 y=383 之下，不撞）
LEFT = 273               # 右栏左边界


def font(name: str = "cn") -> str:
    return "STSong-Light" if name == "cn" else "Helvetica"


# STSong-Light(Adobe-GB1 CID 字体)的字符渲染坑（已全量实测）：
# 1. 不含 U+00B7(·) 与 U+2027(‧) 字形，画到会丢字 → 替换为 U+30FB(片假名中点)。
# 2. 对欧洲重音拉丁字母要么静默丢弃(ç / É / ä / ß → François 变 Franois)，要么以全角汉字宽
#    渲染(ó / ě 导致 Ramón 裂成 Ramó  n) → 统一 NFKD 降级与连字展开为标准 ASCII 拼写。
# 3. 不含上下标(²³⁻₀₁₂)、偏导符号(∂)与超 BMP 生僻汉字(如 106 号元素 𬭳)，画到会静默丢失或
#    破坏文本流(6.02×10²³ 变 6.02×10) → 统一转为可读 ASCII 科学记法与化学符号。
_CN_DOT = "\u30fb"
_SPECIAL_LATIN = {
    "ß": "ss", "Æ": "AE", "æ": "ae", "Œ": "OE", "œ": "oe",
    "Ø": "O", "ø": "o", "Ł": "L", "ł": "l", "Ð": "D", "ð": "d", "Þ": "Th", "þ": "th",
    "đ": "d", "Đ": "D", "ħ": "h", "Ħ": "H", "ı": "i", "İ": "I",
    "ŋ": "n", "Ŋ": "N", "ŧ": "t", "Ŧ": "T",
}
_SUPER_RE = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+")
_SUB_RE = re.compile(r"[₀₁₂₃₄₅₆₇₈₉₊₋]+")
_SUPER_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-")
_SUB_MAP = str.maketrans("₀₁₂₃₄₅₆₇₈₉₊₋", "0123456789+-")
_SPECIAL_SYMBOLS = {
    "\u2027": "\u00b7",
    "\u30fb": "\u00b7",
    "∂": "partial",
    "𬭳": "Sg",
}
_NO_START_PUNCT = frozenset("。，、；：！？）》」』”’…—.,;:!?)]")


TERMINAL = "。！？.!?…」』）\"'»"


def ensure_terminal_punct(text: str) -> str:
    """名言若缺句末标点则补句号；已有则原样返回。"""
    t = (text or "").strip()
    if not t:
        return t
    return t if t[-1] in TERMINAL else t + "。"


def _fix_dot(text, face):
    if face != "cn":
        return text
    text = _SUPER_RE.sub(lambda m: "^" + m.group(0).translate(_SUPER_MAP), text)
    text = _SUB_RE.sub(lambda m: "_" + m.group(0).translate(_SUB_MAP), text)
    out = []
    for ch in text:
        if ord(ch) < 128:
            out.append(ch)
        elif ch in _SPECIAL_SYMBOLS:
            out.append(_SPECIAL_SYMBOLS[ch])
        elif ch in _SPECIAL_LATIN:
            out.append(_SPECIAL_LATIN[ch])
        elif unicodedata.category(ch).startswith("L") and "LATIN" in unicodedata.name(ch, ""):
            decomposed = unicodedata.normalize("NFKD", ch)
            ascii_base = "".join(c for c in decomposed if ord(c) < 128)
            out.append(ascii_base or ch)
        else:
            out.append(ch)
    return "".join(out)


# 混排：ASCII 与 ·×– 走 Helvetica（STSong-Light 对它们给全角/异常宽度，导致"A medeo"、"埃尔温·  薛定谔"、
# "6.02×  10^23"、"1887–  1961" 出现大空隙）；其余字符走 STSong-Light。
_LATIN_EXTRA = frozenset("\u00b7\u00d7\u2013")


def _is_latin(ch):
    return ord(ch) < 128 or ch in _LATIN_EXTRA


def _runs(text):
    runs = []
    for ch in text:
        f = "Helvetica" if _is_latin(ch) else "STSong-Light"
        if runs and runs[-1][0] == f:
            runs[-1][1] += ch
        else:
            runs.append([f, ch])
    return runs


def mixed_width(c, text, size):
    return sum(c.stringWidth(seg, f, size) for f, seg in _runs(text))


def draw_mixed(c, text, x, y, size, align="left"):
    w = mixed_width(c, text, size)
    if align == "right":
        x -= w
    elif align == "center":
        x -= w / 2
    for f, seg in _runs(text):
        c.setFont(f, size)
        c.drawString(x, y, seg)
        x += c.stringWidth(seg, f, size)


def draw_text(c, text, x, y, size, color=INK, face="cn"):
    c.setFillColor(color)
    if face == "cn":
        draw_mixed(c, _fix_dot(text, face), x, y, size)
        return
    c.setFont(font(face), size)
    c.drawString(x, y, text)


def draw_right(c, text, x, y, size, color=INK, face="cn"):
    c.setFillColor(color)
    if face == "cn":
        draw_mixed(c, _fix_dot(text, face), x, y, size, "right")
        return
    c.setFont(font(face), size)
    c.drawRightString(x, y, text)


def draw_centered(c, text, x, y, size, color=INK):
    c.setFillColor(color)
    draw_mixed(c, _fix_dot(text, "cn"), x, y, size, "center")


def wrap_lines(c, text, width, size, face="cn", cap=None):
    c.setFont(font(face), size)
    text = _fix_dot(text, face)
    lines, cur = [], ""
    for ch in text:
        if (mixed_width(c, cur + ch, size) if face == "cn" else c.stringWidth(cur + ch, font(face), size)) <= width:
            cur += ch
        elif ch in _NO_START_PUNCT and len(cur) >= 2:
            # 中文行首避头点：连续跳过行尾右括号/右引号，连同前一个正文字符一起带到下一行
            cut = len(cur) - 1
            while cut > 1 and cur[cut] in _NO_START_PUNCT:
                cut -= 1
            if cut >= 1 and cur[cut] not in _NO_START_PUNCT:
                lines.append(cur[:cut])
                cur = cur[cut:] + ch
            else:
                lines.append(cur)
                cur = ch
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


def draw_mark(c, x, y, size=18, color=INK):
    c.setStrokeColor(color)
    c.setLineWidth(0.85)
    c.circle(x, y, size / 2, stroke=1, fill=0)
    c.setFillColor(color)
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
    # 右上角日期徽章：日期数字居中落在浅色圆章内，避免深色文字压在深色页眉上隐身
    c.setFillColor(accent)
    c.circle(W - 89, H - 57, 36, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont(font("latin"), 19)
    c.drawCentredString(W - 89, H - 64, f"{int(entry[fm['month']]):02d}.{int(entry[fm['day']]):02d}")
    draw_mark(c, 42, H - 52, size=18, color=HexColor("#F0D88D"))
    title = theme.cfg.get("theme", {}).get("name", "主题日历")
    daily_sub = theme.cfg.get("theme", {}).get("dailySubtitle", "DAILY NOTEBOOK")
    draw_text(c, title, 65, H - 51, 17, white)
    draw_text(c, daily_sub, 65, H - 69, 7, HexColor("#B6C0CC"), "latin")

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
    rel_text = theme.get(entry, "relation")
    rel_size = 9
    while rel_size > 6.5 and mixed_width(c, _fix_dot(rel_text, "cn"), rel_size) > 176:
        rel_size -= 0.5
    draw_centered(c, rel_text, cx, cy - 157, rel_size, MUTED)

    left = LEFT
    meta_top = " · ".join(p for p in (theme.get(entry, "relation"), theme.get(entry, "years")) if p)
    if meta_top:
        draw_text(c, meta_top, left, 430, 10, MUTED)
    n = len(name)
    name_size = 40 if n <= 5 else (34 if n <= 7 else (28 if n <= 9 else (23 if n <= 11 else 19)))
    draw_text(c, name, left, 383, name_size)
    meta_sub = " · ".join(p for p in (theme.get(entry, "subtitle"), theme.get(entry, "place")) if p)
    if meta_sub:
        draw_text(c, meta_sub, left, 358, 10, MUTED)

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
    card_top = CARD_BOTTOM  # 底边锚定页脚之上，顶边随内容自适应向上生长

    # ---- 引语 → 来源 → 分隔线 → 故事：严格自上而下，物理上不可能互压 ----
    FLOOR = card_top + box_h + 14
    q_text, q_source = theme.quote(entry, quotes)
    q_text = ensure_terminal_punct(q_text)
    has_src = bool(q_text and q_source)
    lead = 26 if has_src else 23
    q_size = 18 if has_src else 15
    q_color = HexColor("#B85E4C") if has_src else MUTED
    prefix = "“" if has_src else "阅读线索｜"
    suffix = "”" if has_src else ""
    lead_body = q_text or ensure_terminal_punct(theme.get(entry, "tagline"))
    full = prefix + lead_body + suffix
    room = Q_START - FLOOR
    need = 26 if has_src else 0
    max_q = min(max(1, (room - need) // lead), 2 if has_src else 3)
    q_lines = wrap_lines(c, full, 490, q_size, cap=max_q)

    y = Q_START
    c.setFillColor(q_color)
    for line in q_lines:
        draw_mixed(c, line, left, y, q_size)
        y -= lead
    if has_src:
        src_y = y + 8
        src_line = wrap_lines(c, "— " + q_source, 490, 8, cap=1)[0]
        draw_text(c, src_line, left, src_y, 8, MUTED)
        divider_y = src_y - 12
    else:
        divider_y = y + 6
    divider_y = max(divider_y, FLOOR + 6)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(left, divider_y, W - 48, divider_y)

    # 故事：分隔线之下逐行绘制，底线不低于 FLOOR（绝不 re-wrap）
    story_lead = 18
    story_top = max(divider_y - 20, FLOOR + 20)
    max_story = max(0, (story_top - FLOOR) // story_lead + 1)
    if max_story > 0:
        lines = wrap_lines(c, theme.get(entry, "story"), 490, 12)
        if len(lines) > max_story:
            kept = lines[: max_story - 1]
            last = lines[max_story - 1]
            kept.append(last[:max(1, len(last) - 1)] + "…")
        else:
            kept = lines
        for i, line in enumerate(kept):
            y_line = story_top - i * story_lead
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
    unit_label = theme.cfg.get("theme", {}).get("unitLabel", "位人物")
    draw_right(c, f"每天认识一{unit_label}", W - 43, 25, 8, MUTED)
    c.showPage()


def draw_cover(c, theme, count, cfg_path: Path):
    t = theme.cfg.get("theme", {})
    p_cfg = theme.cfg.get("print", {})
    title = t.get("name", "主题日历")
    unit = t.get("unitLabel", "位人物")
    tagline = t.get("tagline", f"每天认识一{unit}。")
    edition_year = datetime.date.today().year
    badge = p_cfg.get("coverBadge", f"精选 {{count}} {unit} · A4 横版打印版").format(count=count)

    c.setFillColor(INK)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    cover_img_raw = p_cfg.get("coverImage")
    cover_img = resolve_cfg_path(cfg_path, cover_img_raw) if cover_img_raw else None
    if cover_img and cover_img.exists():
        image_width = H * 1664 / 936
        c.drawImage(ImageReader(str(cover_img)), 0, 0, image_width, H, preserveAspectRatio=False)
        c.setFillColor(Color(0.05, 0.11, 0.18, alpha=0.24))
        c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(Color(0.03, 0.08, 0.14, alpha=0.72))
        c.roundRect(42, 37, 420, 91, 7, fill=1, stroke=0)
        draw_text(c, badge, 61, 93, 18, HexColor("#F0B29F"))
        c.setStrokeColor(HexColor("#DAB76A"))
        c.line(61, 75, 310, 75)
        draw_text(c, tagline, 61, 54, 11.5, Color(1, 1, 1, alpha=0.78))
        draw_right(c, f"PRINT EDITION · {edition_year}", W - 45, 34, 9, Color(1, 1, 1, alpha=0.68), "latin")
    else:
        c.setStrokeColor(HexColor("#B48C46"))
        c.setLineWidth(0.6)
        for radius in (75, 145, 220):
            c.circle(W - 140, H / 2, radius, stroke=1, fill=0)
        c.setFillColor(HexColor("#F0D88D"))
        c.circle(W - 140, H / 2, 7, fill=1, stroke=0)
        title_size = 44 if len(title) <= 10 else (36 if len(title) <= 14 else 28)
        draw_text(c, title, 61, 310, title_size, white)
        draw_text(c, badge, 61, 250, 18, HexColor("#F0B29F"))
        c.setStrokeColor(HexColor("#DAB76A"))
        c.setLineWidth(0.7)
        c.line(61, 225, 320, 225)
        draw_text(c, tagline, 61, 196, 12, HexColor("#B6C0CC"))
        draw_right(c, f"PRINT EDITION · {edition_year}", W - 45, 40, 9, HexColor("#B6C0CC"), "latin")
    c.showPage()


def draw_overview(c, entries, theme):
    """可选 2 页全年 12 月总览（6 个月/页），每个姓名按子栏宽精准截断，杜绝跨栏压字。"""
    t = theme.cfg.get("theme", {})
    p_cfg = theme.cfg.get("print", {})
    title = t.get("name", "主题日历")
    count_all = len(entries)
    overview_title = p_cfg.get("overviewTitle", "全年纪念日总览")
    overview_sub_tpl = p_cfg.get("overviewSubtitle", "{count} DAILY NOTES")
    foot_left = p_cfg.get("overviewFootNote", "带色点的日期收录了主题人物或历史纪念。")
    foot_right = p_cfg.get("overviewFootRight", f"{title} · 共 {{count}} 条收录").format(count=count_all)

    grouped = {month: [] for month in range(1, 13)}
    for entry in entries:
        grouped[int(entry[theme.fm["month"]])].append(entry)

    for page_start in (1, 7):
        c.setFillColor(PAPER)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        draw_mark(c, 47, H - 47)
        draw_text(c, overview_title, 75, H - 53, 26)
        sub_left = overview_sub_tpl.format(count=count_all)
        draw_text(c, f"{sub_left} · {page_start}-{page_start + 5}", 76, H - 72, 8, MUTED, "latin")

        col_w = (W - 84) / 3
        box_w = col_w - 17
        top = H - 128
        bottom = 46
        row_h = (top - bottom) / 2
        header_h = 38
        list_h = row_h - header_h - 4
        item_h = 15
        per_col = max(1, int(list_h // item_h))

        for offset in range(6):
            month = page_start + offset
            col, row = offset % 3, offset // 3
            x = 42 + col * col_w
            y_top = top - row * row_h
            c.setStrokeColor(LINE)
            c.setLineWidth(0.6)
            c.line(x, y_top, x + box_w, y_top)
            draw_text(c, f"{month:02d}", x, y_top - 22, 17, INK, "latin")
            draw_text(c, "月", x + 27, y_top - 20, 11, MUTED)
            entries_m = grouped[month]
            m_count = len(entries_m)
            draw_right(c, f"{m_count} 人", x + box_w, y_top - 20, 9, MUTED)

            ncol = max(1, (m_count + per_col - 1) // per_col)
            inner_col_w = (box_w - 8) / ncol
            name_avail = max(14.0, inner_col_w - 20.0)
            for i, entry in enumerate(entries_m):
                cc = i // per_col
                rr = i % per_col
                ex = x + 4 + cc * inner_col_w
                ey = y_top - header_h - rr * item_h
                accent = ACCENTS.get(entry.get("color", "blue"), ACCENTS["blue"])
                c.setFillColor(accent)
                c.circle(ex, ey + 3, 2.5, fill=1, stroke=0)
                draw_text(c, f"{int(entry[theme.fm['day']]):02d}", ex + 6, ey, 7, MUTED, "latin")
                raw_name = _fix_dot(theme.get(entry, "name"), "cn")
                shown = ""
                for ch in raw_name:
                    if mixed_width(c, shown + ch, 6) > name_avail:
                        break
                    shown += ch
                draw_text(c, shown, ex + 17, ey, 6, INK)

        draw_text(c, foot_left, 42, 29, 9, MUTED)
        draw_right(c, foot_right, W - 42, 29, 9, MUTED)
        c.showPage()


def draw_print_notes(c, theme, count):
    """可选版权与印刷说明页（全主题文案驱动，不含草稿样稿话术）。"""
    t = theme.cfg.get("theme", {})
    p_cfg = theme.cfg.get("print", {})
    title = t.get("name", "主题日历")
    unit = t.get("unitLabel", "位人物")
    edition_year = datetime.date.today().year
    notes_sub = p_cfg.get("printNotesEdition", "PRINTING NOTES · PRINT EDITION")
    content_note = p_cfg.get(
        "printNotesContent",
        f"本册收录精选 {{count}} {unit}，全部条目均已完成日期与资料核验，可直接用于桌面翻阅或打印装帧。",
    ).format(count=count)
    banner_sub = p_cfg.get("printNotesBannerSub", "本册由主题日历通用排版引擎自动生成并通过几何体检。")

    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    draw_mark(c, 48, H - 49)
    draw_text(c, "版权与印刷说明", 76, H - 54, 27)
    draw_text(c, notes_sub, 76, H - 74, 8, MUTED, "latin")

    blocks = [
        ("建议规格", "A4 横向，100% 实际大小。单页打印可直接作为展示卡；双面装订建议选择短边翻转。"),
        ("纸张建议", "日常打印可用 100-120g 书写纸；做成桌面卡或礼品册时，建议使用 160-200g 哑光卡纸。"),
        ("装订与裁切", "保留页面白边用于装订或裁切。若采用活页夹，可在左侧预留打孔边；不建议勾选“适合页面”。"),
        ("内容说明", content_note),
    ]
    y = H - 135
    for index, (heading, text) in enumerate(blocks, start=1):
        c.setFillColor(ACCENTS[("coral", "blue", "green", "gold")[index - 1]])
        c.circle(67, y + 10, 16, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont(font("latin"), 9)
        c.drawCentredString(67, y + 6, f"{index:02d}")
        draw_text(c, heading, 103, y + 10, 16)
        lines = wrap_lines(c, text, 610, 11)
        ty = y - 16
        for line in lines:
            draw_text(c, line, 103, ty, 11, MUTED)
            ty -= 18
        y = ty - 26
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(103, y + 9, W - 58, y + 9)
        y -= 18

    c.setFillColor(INK)
    c.roundRect(57, 52, W - 114, 52, 6, fill=1, stroke=0)
    draw_text(c, f"{title} · 精选 {count} {unit} · {edition_year} 版", 77, 81, 12, white)
    draw_text(c, banner_sub, 77, 62, 9, HexColor("#B6C0CC"))
    c.showPage()


def draw_back_cover(c, theme):
    t = theme.cfg.get("theme", {})
    p_cfg = theme.cfg.get("print", {})
    title = t.get("name", "主题日历")
    unit = t.get("unitLabel", "位人物")
    subtitle = t.get("subtitle", f"每天认识一{unit}")
    lines = t.get("backCoverLines", ["把今天的好奇", "留给明天的问题。"])
    back_url = p_cfg.get("backCoverUrl", "")
    edition_year = datetime.date.today().year

    c.setFillColor(INK)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setStrokeColor(HexColor("#B48C46"))
    c.setLineWidth(0.7)
    for radius in (65, 125, 190, 265):
        c.circle(W - 128, H / 2, radius, stroke=1, fill=0)
    c.setFillColor(HexColor("#F0D88D"))
    c.circle(W - 128, H / 2, 8, fill=1, stroke=0)
    if len(lines) >= 1:
        draw_text(c, lines[0], 70, 325, 33, white)
    if len(lines) >= 2:
        draw_text(c, lines[1], 70, 276, 33, white)
    c.setStrokeColor(HexColor("#DAB76A"))
    c.line(70, 236, 313, 236)
    draw_text(c, title, 70, 195, 18, HexColor("#F0D88D"))
    draw_text(c, subtitle, 70, 170, 11, HexColor("#B6C0CC"))
    if back_url:
        draw_text(c, back_url, 70, 72, 10, HexColor("#B6C0CC"), "latin")
    draw_right(c, f"PRINT EDITION · {edition_year}", W - 45, 42, 8, HexColor("#B6C0CC"), "latin")
    c.showPage()


def resolve_cfg_path(cfg_path: Path, raw: str, *, prefer_config_dir: bool = False) -> Path:
    """支持相对 --config 所在目录或当前工作目录解析路径，消除换目录即报错的脆弱性。"""
    p = Path(raw)
    if p.is_absolute():
        return p
    from_cfg = (cfg_path.parent / p).resolve()
    if prefer_config_dir or from_cfg.exists():
        return from_cfg
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg_path = Path(args.config).resolve()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    theme = Theme(cfg)
    entry_path = resolve_cfg_path(cfg_path, cfg["entryFile"])
    cfg_relative_mode = (not Path(cfg["entryFile"]).is_absolute()) and entry_path == (cfg_path.parent / cfg["entryFile"]).resolve()
    entries = json.loads(entry_path.read_text(encoding="utf-8"))
    quotes = json.loads(resolve_cfg_path(cfg_path, cfg["quoteFile"]).read_text(encoding="utf-8")) if cfg.get("quoteFile") else {}
    entries.sort(key=lambda e: (int(e[theme.fm["month"]]), int(e[theme.fm["day"]]), theme.get(e, "name")))

    out_dir = resolve_cfg_path(cfg_path, cfg.get("outputDir", "output/pdf"), prefer_config_dir=cfg_relative_mode)
    p_cfg = cfg.get("print", {})
    default_name = p_cfg.get("dailyFilename", "{title}_每日版_A4.pdf").format(
        title=cfg["theme"].get("name", "主题日历"),
        count=len(entries),
    )
    out = Path(args.out) if args.out else (out_dir / default_name)
    out.parent.mkdir(parents=True, exist_ok=True)

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    c = canvas.Canvas(str(out), pagesize=(W, H), pageCompression=1)
    c.setTitle(f"{cfg['theme'].get('name','主题日历')} - 每日版")
    draw_cover(c, theme, len(entries), cfg_path)
    if p_cfg.get("includeOverview"):
        draw_overview(c, entries, theme)
    total = len(entries)
    for i, entry in enumerate(entries, start=1):
        draw_entry(c, entry, theme, quotes, i, total)
    if p_cfg.get("includePrintNotes"):
        draw_print_notes(c, theme, total)
    draw_back_cover(c, theme)
    c.save()
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
