#!/usr/bin/env python3
"""主题日历「月度缩览版」PDF 生成器（一人一行：日期 + 名字 + 名言）。

用法：
  python generate_monthly_pdf.py --config theme.json [--out output/pdf/月度版.pdf]

版面：纵向 A4 + 三栏先列后行流式排版；某月条目过多时自动续页（页眉标注「续」）。
本文件已内建本项目踩过的坑（见 SKILL.md），改字段映射即可换主题，不必改代码。
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import unicodedata
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
# 米白纸上作为数字字色时，使用同色系高对比度印刷色（WCAG >= 4.5:1），避免淡粉彩发虚
DAY_ACCENTS = {
    "blue": HexColor("#3A6888"), "coral": HexColor("#B85844"),
    "gold": HexColor("#9C7422"), "green": HexColor("#447452"),
    "violet": HexColor("#6A568C"),
}

MARGIN, COL_GAP, N_COLS = 40, 16, 3
CONTENT_TOP = H - 96
CONTENT_BOTTOM = 44
HEADER_LINE = H - 90
NAME_SIZE, DAY_SIZE, QUOTE_SIZE, QUOTE_LEAD = 11, 13, 8, 11
DAY_NAME_BASE = 13      # 日期/名字基线 = y_top - 13
QUOTE_BASE_GAP = 13      # 名言首行基线 = y_top - 26（与日期行留净空，防压字）
BOTTOM_GAP = 7


def choose_layout(cfg: dict, max_month_count: int) -> dict:
    """根据月均条目密度选择栏数与字号：小体量精选版自动切单栏/双栏，避免三栏留白三分之二。"""
    raw = cfg.get("monthlyColumns", "auto")
    if raw in (1, 2, 3):
        n_cols = int(raw)
    elif max_month_count <= 10:
        n_cols = 1
    elif max_month_count <= 20:
        n_cols = 2
    else:
        n_cols = 3

    if n_cols == 1:
        return {
            "n_cols": 1, "col_gap": 0,
            "day_size": 16, "name_size": 13.5, "quote_size": 9.5, "quote_lead": 14,
            "card_size": 8.5, "card_gap": 13,
            "day_name_base": 16, "quote_base_gap": 17, "bottom_gap": 22, "cap": 2,
            "show_meta": True, "show_card": True, "divider": True,
        }
    if n_cols == 2:
        return {
            "n_cols": 2, "col_gap": 22,
            "day_size": 13, "name_size": 11.5, "quote_size": 8.5, "quote_lead": 12,
            "card_size": 0, "card_gap": 0,
            "day_name_base": 13, "quote_base_gap": 14, "bottom_gap": 11, "cap": 2,
            "show_meta": False, "show_card": False, "divider": False,
        }
    return {
        "n_cols": 3, "col_gap": COL_GAP,
        "day_size": DAY_SIZE, "name_size": NAME_SIZE, "quote_size": QUOTE_SIZE, "quote_lead": QUOTE_LEAD,
        "card_size": 0, "card_gap": 0,
        "day_name_base": DAY_NAME_BASE, "quote_base_gap": QUOTE_BASE_GAP, "bottom_gap": BOTTOM_GAP, "cap": 2,
        "show_meta": False, "show_card": False, "divider": False,
    }


def font(name: str = "cn") -> str:
    return "STSong-Light" if name == "cn" else "Helvetica"


# STSong-Light(Adobe-GB1 CID 字体)有两个拉丁/符号渲染坑：
# 1. 不含 U+00B7(MIDDLE DOT)字形，画到 · 会丢字 → 替换为 U+30FB(片假名中点)。
# 2. 对欧洲重音拉丁字母要么静默丢弃(ç / É / ä / ß → François 变 Franois)，要么以全角汉字宽
#    渲染(ó / ě 导致 Ramón 裂成 Ramó  n) → 统一 NFKD 降级与连字展开为标准 ASCII 拼写。
_CN_DOT = "\u30fb"
_SPECIAL_LATIN = {
    "ß": "ss", "Æ": "AE", "æ": "ae", "Œ": "OE", "œ": "oe",
    "Ø": "O", "ø": "o", "Ł": "L", "ł": "l", "Ð": "D", "ð": "d", "Þ": "Th", "þ": "th",
}
_NO_START_PUNCT = frozenset("。，、；：！？）》」』”’…—.,;:!?)]")


def _fix_dot(text, face):
    if face != "cn":
        return text
    text = text.replace("\u00b7", _CN_DOT)
    out = []
    for ch in text:
        if ord(ch) < 128:
            out.append(ch)
        elif ch in _SPECIAL_LATIN:
            out.append(_SPECIAL_LATIN[ch])
        elif unicodedata.category(ch).startswith("L") and "LATIN" in unicodedata.name(ch, ""):
            decomposed = unicodedata.normalize("NFKD", ch)
            ascii_base = "".join(c for c in decomposed if ord(c) < 128)
            out.append(ascii_base or ch)
        else:
            out.append(ch)
    return "".join(out)


# 句子结尾标点：没有结尾标点则补句号（中文语境优先）。
_TERMINAL = "。！？.!?…」』）\"'»●"
_PLACEHOLDER = "—"


def ensure_terminal_punct(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return _PLACEHOLDER
    if t[-1] in _TERMINAL:
        return t
    return t + "。"


def draw_text(c, text, x, y, size, color=INK, face="cn"):
    c.setFillColor(color)
    c.setFont(font(face), size)
    c.drawString(x, y, _fix_dot(text, face))


def draw_right(c, text, x, y, size, color=INK, face="cn"):
    c.setFillColor(color)
    c.setFont(font(face), size)
    c.drawRightString(x, y, _fix_dot(text, face))


def wrap_lines(c, text, width, size, face="cn", cap=None):
    c.setFont(font(face), size)
    text = _fix_dot(text, face)
    lines, cur = [], ""
    for ch in text:
        if c.stringWidth(cur + ch, font(face), size) <= width:
            cur += ch
        elif ch in _NO_START_PUNCT and len(cur) >= 2:
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
            text = q["text"]
        elif isinstance(q, str) and q.strip():
            text = q
        else:
            text = self.get(entry, "tagline", "—")
        text = (text or "").strip()
        if not text:
            return _PLACEHOLDER
        return ensure_terminal_punct(text)


def _card_summary(entry, theme):
    card_a = theme.get(entry, "cardA")
    if not card_a:
        return ""
    label = theme.cfg.get("labels", {}).get("cardA", "核心贡献")
    return f"{label}：{card_a}"


def block_height(c, entry, theme, quotes, col_w, layout):
    """区块高度 —— 排版(pack)与绘制(draw)必须共用这一个函数与同一套 layout 参数。

    坑：曾经排版用一套高度、绘制用另一套(高 12pt)，导致最忙月份的末条被挤出页底。
    """
    quote_w = col_w - (4 if layout["n_cols"] == 1 else 12)
    lines = wrap_lines(c, theme.quote_of(entry, quotes), quote_w, layout["quote_size"], cap=layout["cap"])
    n = len(lines)
    ink_top = 3
    q_first = layout["day_name_base"] + layout["quote_base_gap"]
    last_base = q_first + (n - 1) * layout["quote_lead"]
    if layout.get("show_card") and _card_summary(entry, theme):
        last_base += layout["card_gap"]
    ink_bottom = last_base + 2
    return (ink_bottom - ink_top) + layout["bottom_gap"], lines


def pack_month(c, entries, theme, quotes, col_w, layout):
    """先列后行：先填满第 0 栏(从上到下)，再填第 1 栏，再填第 2 栏；满页则续页。
    阅读顺序 = col0 上→下、col1 上→下、col2 上→下，与排序序一致(非横向散排)。"""
    n_cols = layout["n_cols"]
    col_gap = layout["col_gap"]
    col_x = [MARGIN + i * (col_w + col_gap) for i in range(n_cols)]
    pages, cols = [], [[] for _ in range(n_cols)]
    col_y = [CONTENT_TOP] * n_cols
    ci = 0
    for entry in entries:
        h, _ = block_height(c, entry, theme, quotes, col_w, layout)
        while col_y[ci] - h < CONTENT_BOTTOM:
            if ci < n_cols - 1:
                ci += 1
            else:
                pages.append((cols, col_x[:]))
                cols = [[] for _ in range(n_cols)]
                col_y = [CONTENT_TOP] * n_cols
                ci = 0
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
    draw_right(c, f"{title} · 月度版", W - MARGIN, H - 76, 8, MUTED)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(MARGIN, HEADER_LINE, W - MARGIN, HEADER_LINE)


def draw_block(c, entry, x, y_top, col_w, theme, quotes, layout):
    accent = DAY_ACCENTS.get(entry.get("color", "blue"), DAY_ACCENTS["blue"])
    day = f"{int(entry[theme.fm['day']]):02d}"
    name = theme.get(entry, "name")
    day_size = layout["day_size"]
    name_size = layout["name_size"]
    base_y = y_top - layout["day_name_base"]

    meta_text = ""
    meta_w = 0.0
    if layout["show_meta"]:
        meta_text = "·".join(
            p for p in (theme.get(entry, "years"), theme.get(entry, "field"), theme.get(entry, "place")) if p
        )
        if meta_text:
            meta_w = c.stringWidth(_fix_dot(meta_text, "cn"), font("cn"), 8.5) + 14

    # 坑：超长名字会越出本栏、压到邻栏文字。必须按栏宽缩字号，仍放不下就截断。
    day_w = c.stringWidth(day, font("latin"), day_size)
    gap = 8 if layout["n_cols"] == 1 else 6
    avail = col_w - day_w - gap - 4 - meta_w
    size, shown = name_size, _fix_dot(name, "cn")
    c.setFont(font("cn"), size)
    while size >= 7:
        if c.stringWidth(shown, font("cn"), size) <= avail:
            break
        size -= 1
    else:
        cur = ""
        for ch in shown:
            if c.stringWidth(cur + ch + "…", font("cn"), 7) > avail:
                break
            cur += ch
        shown, size = cur + "…", 7

    draw_text(c, day, x, base_y, day_size, accent, "latin")
    draw_text(c, shown, x + day_w + gap, base_y, size, INK)
    if meta_text:
        draw_right(c, meta_text, x + col_w, base_y + 1, 8.5, MUTED)

    quote_w = col_w - (4 if layout["n_cols"] == 1 else 12)
    lines = wrap_lines(c, theme.quote_of(entry, quotes), quote_w, layout["quote_size"], cap=layout["cap"])
    qy = base_y - layout["quote_base_gap"]
    for i, line in enumerate(lines):
        draw_text(c, line, x, qy - i * layout["quote_lead"], layout["quote_size"], INK if layout["n_cols"] == 1 else MUTED)
    last_y = qy - (len(lines) - 1) * layout["quote_lead"]

    if layout.get("show_card"):
        summary = _card_summary(entry, theme)
        if summary:
            last_y -= layout["card_gap"]
            card_lines = wrap_lines(c, summary, quote_w, layout["card_size"], cap=1)
            draw_text(c, card_lines[0], x, last_y, layout["card_size"], MUTED)

    if layout["divider"]:
        rule_y = last_y - 10
        c.setStrokeColor(LINE)
        c.setLineWidth(0.45)
        c.line(x, rule_y, x + col_w, rule_y)


def draw_footer(c, page_no, total, unit_label="位人物"):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(MARGIN, 30, W - MARGIN, 30)
    draw_text(c, f"第 {page_no:02d} 页 / 共 {total:02d} 页", MARGIN, 18, 8, MUTED)
    # 坑：页脚文案必须主题无关。曾硬编码「每天认识一位科学家」，导致医学/文学等
    # 主题日历页脚串味。unitLabel 形如「位人物」「位医者」，拼在「每天认识一」之后。
    draw_right(c, f"每天认识一{unit_label}", W - MARGIN, 18, 8, MUTED)


def unit_noun(theme_cfg: dict) -> str:
    """从配置提取不带量词的人物名词（如「位医者」→「医者」），避免封面拼出「出生的位医者们」。"""
    if theme_cfg.get("unitNoun"):
        return str(theme_cfg["unitNoun"]).strip()
    label = str(theme_cfg.get("unitLabel", "位人物")).strip()
    if len(label) >= 2 and label[0] in "位名个颗座":
        return label[1:]
    return label or "人物"


def resolve_cfg_path(cfg_path: Path, raw: str, *, prefer_config_dir: bool = False) -> Path:
    """支持相对 --config 所在目录或当前工作目录解析路径，消除换目录即报错的脆弱性。"""
    p = Path(raw)
    if p.is_absolute():
        return p
    from_cfg = (cfg_path.parent / p).resolve()
    if prefer_config_dir or from_cfg.exists():
        return from_cfg
    return p


def draw_cover(c, theme):
    c.setFillColor(INK)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor("#F0D88D"))
    c.circle(W / 2, 250, 60, fill=1, stroke=0)
    t = theme.cfg.get("theme", {})
    title = t.get("name", "主题日历")
    title_size = 38 if len(title) <= 10 else (31 if len(title) <= 13 else 25)
    draw_text(c, title, 70, 470, title_size, HexColor("#F7F1E7"))
    draw_text(c, "月度生日版", 70, 422, 24, HexColor("#F0D88D"))
    draw_text(c, f"每个月，认识在这个月出生的{unit_noun(t)}们——", 70, 372, 12, HexColor("#B6C0CC"))
    draw_text(c, "以及他们留下的那句话。", 70, 352, 12, HexColor("#B6C0CC"))
    draw_text(c, "生日 · 名字 · 名言", 70, 318, 13, HexColor("#F0B29F"))
    draw_text(c, f"PRINT EDITION · {datetime.date.today().year}", W - 160, 40, 8, HexColor("#B6C0CC"), "latin")
    c.showPage()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="主题配置 JSON")
    ap.add_argument("--out", default=None, help="输出 PDF 路径")
    args = ap.parse_args()

    cfg_path = Path(args.config).resolve()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    theme = Theme(cfg)
    entry_path = resolve_cfg_path(cfg_path, cfg["entryFile"])
    cfg_relative_mode = (not Path(cfg["entryFile"]).is_absolute()) and entry_path == (cfg_path.parent / cfg["entryFile"]).resolve()
    entries = json.loads(entry_path.read_text(encoding="utf-8"))
    quotes = json.loads(resolve_cfg_path(cfg_path, cfg["quoteFile"]).read_text(encoding="utf-8")) if cfg.get("quoteFile") else {}
    entries.sort(key=lambda e: (int(e[theme.fm["month"]]), int(e[theme.fm["day"]]), theme.get(e, "name")))

    by_month = {m: [] for m in range(1, 13)}
    for e in entries:
        by_month[int(e[theme.fm["month"]])].append(e)

    out_dir = resolve_cfg_path(cfg_path, cfg.get("outputDir", "output/pdf"), prefer_config_dir=cfg_relative_mode)
    out = Path(args.out) if args.out else (out_dir / f"{cfg['theme'].get('name','主题日历')}_月度生日版_A4.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    c = canvas.Canvas(str(out), pagesize=(W, H), pageCompression=1)
    c.setTitle(f"{cfg['theme'].get('name','主题日历')} - 月度生日版")
    draw_cover(c, theme)

    max_month_count = max((len(v) for v in by_month.values()), default=0)
    layout = choose_layout(cfg, max_month_count)
    n_cols = layout["n_cols"]
    col_w = (W - 2 * MARGIN - (n_cols - 1) * layout["col_gap"]) / n_cols
    schedule = [(m, pack_month(c, by_month[m], theme, quotes, col_w, layout)) for m in range(1, 13)]
    total_pages = sum(len(p) for _, p in schedule)

    page_no = 0
    for month, pages in schedule:
        for pi, (cols, col_x) in enumerate(pages):
            page_no += 1
            draw_header(c, month, len(by_month[month]), theme, continuation=pi > 0)
            for ci, col_entries in enumerate(cols):
                y = CONTENT_TOP
                for entry in col_entries:
                    h, _ = block_height(c, entry, theme, quotes, col_w, layout)
                    draw_block(c, entry, col_x[ci], y, col_w, theme, quotes, layout)
                    y -= h
            draw_footer(c, page_no, total_pages, theme.cfg.get("theme", {}).get("unitLabel", "位人物"))
            c.showPage()
    c.save()
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
