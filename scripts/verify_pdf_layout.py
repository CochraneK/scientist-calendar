"""PDF 排版体检：几何方式检测「文字压字 / 越界 / 卡片内混入外来文字」。

为什么需要它：
  生成 PDF 时（尤其是中文 + 复杂版面），重叠/溢出用肉眼很难全量检查；
  而本环境往往无法查看渲染图。这个脚本用 PyMuPDF 读取
    - get_text("words")  -> 每个词的包围盒
    - get_drawings()     -> 填充矩形（如底部的「核心贡献/你知道吗」卡片）
  纯几何判断，不依赖看图，可全量自动化，是主题日历迁移时的核心验收工具。

用法：
  python scripts/verify_pdf_layout.py <pdf> [选项]

常用选项：
  --card-color F0EBE1   卡片填充色(十六进制, 不带#)，用于「卡片内混外来文字」检测
  --allow-in-card 核心贡献,你知道吗
                        允许出现在卡片内的文字（卡片自身的标签/正文前缀），
                        其余落入卡片的词会被判定为「外来文字泄漏」
  --header-y 90         页眉区下沿(pymupdf 坐标：从页顶往下)，小于它算撞页眉
  --floor-y 798         内容区下沿(pymupdf 坐标)，大于它算越出内容区
  --footer-y 808        大于它算页脚区（页脚页码是合法内容，不参与比对）
  --th 1.2              判定为真正压字的最小重叠边长(pt)，避免相邻贴边误报
  --max-report 20       每类最多打印多少条
  --quiet               只打印汇总行（适合 CI）

退出码：0 = 无问题；1 = 发现问题（便于 CI 拦截）

坐标说明（易踩坑）：
  PyMuPDF 的 get_text("words") 返回 (x0, y0, x1, y1)，**原点在左上角，y 向下增长**；
  而 reportlab 画图时 **原点在左下角，y 向上增长**。换算：reportlab_y = 页高 - pymupdf_y。
  本脚本内部统一用 pymupdf 坐标（y 向下），所以「页眉」是小 y、「页脚」是大 y。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    sys.exit("需要 PyMuPDF：pip install pymupdf")


def hex_to_rgb(value: str) -> tuple[float, float, float]:
    v = value.strip().lstrip("#")
    if len(v) != 6:
        raise argparse.ArgumentTypeError(f"颜色必须是 6 位十六进制，如 F0EBE1，收到：{value}")
    return tuple(int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def find_card_rects(page, rgb: tuple[float, float, float], tol: float = 0.02):
    """找出用指定颜色填充的矩形（即版面上的卡片/色块）。"""
    rects = []
    for d in page.get_drawings():
        if not d.get("fill"):
            continue
        fr, fg, fb = d["fill"][:3]
        if abs(fr - rgb[0]) < tol and abs(fg - rgb[1]) < tol and abs(fb - rgb[2]) < tol:
            r = d["rect"]
            rects.append(r)
    return rects


def in_any_rect(word, rects, slop: float = 1.0) -> bool:
    x0, y0, x1, y1 = word[:4]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2  # 用中心点判定，避免跨边界误判
    return any(r.x0 - slop <= cx <= r.x1 + slop and r.y0 - slop <= cy <= r.y1 + slop for r in rects)


def verify(
    pdf_path: Path,
    card_rgb: tuple[float, float, float] | None,
    allow_in_card: list[str],
    ratio_header: float,
    ratio_floor: float,
    ratio_footer: float,
    th: float,
    header_y: float | None = None,
    floor_y: float | None = None,
    footer_y: float | None = None,
    check_bounds: bool = False,
    check_tofu: bool = True,
):
    doc = fitz.open(pdf_path)
    pairwise: list[tuple] = []
    leaks: list[tuple] = []
    oob: list[tuple] = []
    tofu: list[tuple] = []

    for pno in range(doc.page_count):
        page = doc[pno]
        # 豆腐块检测：中文被交给无中文字形的字体(如 Helvetica)渲染时，
        # 提取出来会变成连续的 "I"。这类问题肉眼在页面上很难发现（看着像乱码），
        # 但压字检测完全查不出来。
        if check_tofu:
            text = page.get_text()
            bad = re.findall(r"I{3,}", text)
            if bad:
                tofu.append((pno + 1, bad[:3], "中文可能用了拉丁字体渲染"))
        h = page.rect.height
        # 每页按自身高度推导边界 —— 同一份 PDF 可能有横版/纵版混排
        hy = header_y if header_y is not None else ratio_header * h
        fy = floor_y if floor_y is not None else h - ratio_floor * h
        fty = footer_y if footer_y is not None else h - ratio_footer * h

        words = page.get_text("words")
        cards = find_card_rects(page, card_rgb) if card_rgb else []

        for i, wi in enumerate(words):
            # 1) 卡片内混入外来文字
            if cards and in_any_rect(wi, cards):
                if not any(a in wi[4] for a in allow_in_card):
                    leaks.append((pno + 1, wi[4], round(wi[0], 1), round(wi[1], 1)))
            # 2) 越界（默认关闭；排除页脚区：页脚页码是合法内容）
            if check_bounds and not (wi[3] > fty) and (wi[1] < hy or wi[3] > fy):
                oob.append((pno + 1, wi[4], round(wi[1], 1), round(wi[3], 1)))
            # 3) 两两压字
            for wj in words[i + 1:]:
                if wi[3] > fty or wj[3] > fty:
                    continue
                ox = min(wi[2], wj[2]) - max(wi[0], wj[0])
                oy = min(wi[3], wj[3]) - max(wi[1], wj[1])
                if ox > th and oy > th:
                    pairwise.append(
                        (pno + 1, wi[4], wj[4], round(ox, 1), round(oy, 1))
                    )

    total = len(pairwise) + len(leaks) + len(oob) + len(tofu)
    return doc.page_count, pairwise, leaks, oob, tofu, total


def main() -> int:
    ap = argparse.ArgumentParser(description="PDF 排版几何体检（压字/越界/卡片泄漏）")
    ap.add_argument("pdf", help="待检查的 PDF 路径")
    ap.add_argument("--card-color", default=None, help="卡片填充色，如 F0EBE1")
    ap.add_argument(
        "--allow-in-card",
        default="",
        help="允许出现在卡片内的文字，逗号分隔；也可用 --allow-file 传大量词条",
    )
    ap.add_argument(
        "--allow-file",
        default=None,
        help="卡片内允许文字清单（每行一条）。卡片正文很多时用它，"
             "可由数据集脚本生成（如把所有 contribution/fact 导成一行条）",
    )
    # 边界既可按比例自动推导（适配横版/纵版混排），也可显式覆盖
    ap.add_argument("--ratio-header", type=float, default=0.11, help="页眉区下沿 = 该比例 × 页高")
    ap.add_argument("--ratio-floor", type=float, default=0.055, help="内容区下沿距页底 = 该比例 × 页高")
    ap.add_argument("--ratio-footer", type=float, default=0.030, help="页脚区起点距页底 = 该比例 × 页高")
    ap.add_argument(
        "--check-bounds",
        action="store_true",
        help="启用越界检测。默认关闭：页眉/页脚位置因版面而异，"
             "通用阈值容易把「设计上就该在顶部/底部的文字」误报，"
             "需要按自己版面的实际数值调 --header-y/--floor-y/--footer-y 后再开",
    )
    ap.add_argument("--header-y", type=float, default=None, help="显式指定页眉下沿(覆盖比例推导)")
    ap.add_argument("--floor-y", type=float, default=None, help="显式指定内容区下沿(覆盖比例推导)")
    ap.add_argument("--footer-y", type=float, default=None, help="显式指定页脚区起点(覆盖比例推导)")
    ap.add_argument("--th", type=float, default=1.2, help="压字判定阈值(pt)")
    ap.add_argument(
        "--check-tofu",
        dest="check_tofu",
        action="store_true",
        default=True,
        help="启用豆腐块(中文用拉丁字体渲染成连续 I)检测（默认开）",
    )
    ap.add_argument(
        "--no-check-tofu",
        dest="check_tofu",
        action="store_false",
        help="关闭豆腐块检测",
    )
    ap.add_argument("--max-report", type=int, default=20)
    ap.add_argument("--quiet", action="store_true", help="只输出汇总")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        sys.exit(f"找不到 PDF：{pdf_path}")

    card_rgb = hex_to_rgb(args.card_color) if args.card_color else None
    allow = [s.strip() for s in args.allow_in_card.split(",") if s.strip()]
    if args.allow_file:
        p = Path(args.allow_file)
        if not p.exists():
            sys.exit(f"找不到 allow-file：{p}")
        allow += [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]

    pages, pairwise, leaks, oob, tofu, total = verify(
        pdf_path,
        card_rgb,
        allow,
        args.ratio_header,
        args.ratio_floor,
        args.ratio_footer,
        args.th,
        args.header_y,
        args.floor_y,
        args.footer_y,
        check_bounds=args.check_bounds,
        check_tofu=args.check_tofu,
    )

    if not args.quiet:
        print(f"文件：{pdf_path.name}   页数：{pages}")
        if card_rgb:
            preview = allow[:8]
            print(f"卡片色：#{args.card_color}   卡片内允许词条：{len(allow)} 条"
                  f"（示例：{preview}{'…' if len(allow) > 8 else ''}）")
        print("-" * 66)

    def report(title: str, rows: list[tuple]):
        if not args.quiet:
            print(f"{title}：{len(rows)}")
            for r in rows[: args.max_report]:
                print("   ", r)
            if len(rows) > args.max_report:
                print(f"    … 另有 {len(rows) - args.max_report} 条")
            print()

    report("卡片内混入外来文字", leaks)
    report("内容越界（撞页眉/越内容底线）", oob)
    report("两两文字压字", pairwise)
    report("豆腐块（中文用拉丁字体渲染成连续 I）", tofu)

    status = "✓ 通过" if total == 0 else f"✗ 发现 {total} 处"
    print(f"== 汇总：{status}（压字 {len(pairwise)} / 越界 {len(oob)} / 卡片泄漏 {len(leaks)} / 豆腐块 {len(tofu)}）==")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
