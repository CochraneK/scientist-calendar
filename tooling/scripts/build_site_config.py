#!/usr/bin/env python3
"""从根目录 theme.json 提取 site.* + labels.* 段，生成前端可 import 的 siteConfig.json。

为什么需要它：网页（app/ + tooling/pages/）与分享海报（src/lib/posterCanvas.ts）
的所有主题文案必须与 PDF 生成器（theme.json）共用同一份配置，否则改主题会出现
「PDF 换了名字、网页还是旧的」串味。此脚本在 npm run build / build:pages 之前运行。

用法：
  python -X utf8 tooling/scripts/build_site_config.py           # 写入 src/domain/siteConfig.json
  python -X utf8 tooling/scripts/build_site_config.py --check   # CI 校验（零 diff 才通过）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THEME = ROOT / "theme.json"
OUT = ROOT / "src" / "domain" / "siteConfig.ts"


def build_config(theme: dict) -> dict:
    t = theme.get("theme", {})
    s = theme.get("site", {})
    labels = theme.get("labels", {})
    fields = s.get("fields", [])
    return {
        "name": t.get("name", "主题日历"),
        "nameEn": t.get("nameEn", "Theme Calendar"),
        "unitLabel": t.get("unitLabel", "位人物"),
        "description": t.get("description", f"{t.get('name', '主题日历')}：每天认识一{t.get('unitLabel', '位人物')}。"),
        "origin": s.get("origin", "https://example.github.io"),
        "basePath": s.get("basePath", "/theme-calendar"),
        "entryRouteSegment": s.get("entryRouteSegment", "entries"),
        "icsFilename": s.get("icsFilename", "theme-calendar.ics"),
        "dailyPdfPattern": s.get("dailyPdfPattern", "{name}_每日版_A4.pdf"),
        "monthlyPdfFilename": s.get("monthlyPdfFilename", "{name}_月度生日版_A4.pdf"),
        "posterSlogan": s.get("posterSlogan", t.get("subtitle", "")),
        "posterSiteTag": s.get("posterSiteTag", ""),
        "fields": fields,
        "fallbackEntryId": s.get("fallbackEntryId", ""),
        "illustrations": s.get("illustrations", {}),
        "heroEyebrow": s.get("heroEyebrow", ""),
        "heroTitle": s.get("heroTitle", ""),
        "heroText": s.get("heroText", ""),
        "heroDiscSuffix": s.get("heroDiscSuffix", ""),
        "fieldCountLabel": s.get("fieldCountLabel", ""),
        "entryCountLabel": s.get("entryCountLabel", ""),
        "monthTip": s.get("monthTip", ""),
        "monthTitle": s.get("monthTitle", "月历"),
        "monthSectionLabel": s.get("monthSectionLabel", ""),
        "exploreTitle": s.get("exploreTitle", ""),
        "searchPlaceholder": s.get("searchPlaceholder", ""),
        "searchAriaLabel": s.get("searchAriaLabel", ""),
        "filterAriaLabel": s.get("filterAriaLabel", ""),
        "manifestoEyebrow": s.get("manifestoEyebrow", ""),
        "manifestoHtml": s.get("manifestoHtml", ""),
        "manifestoSub": s.get("manifestoSub", ""),
        "emptySearchTip": s.get("emptySearchTip", ""),
        "archiveEyebrowPrefix": s.get("archiveEyebrowPrefix", ""),
        "entryIndexPrefix": s.get("entryIndexPrefix", ""),
        "entryIndexSuffix": s.get("entryIndexSuffix", ""),
        "footerSummaryPattern": s.get("footerSummaryPattern", ""),
        "labels": {
            "cardA": labels.get("cardA", "核心贡献"),
            "cardB": labels.get("cardB", "你知道吗"),
            "quoteLabel": labels.get("quoteLabel", "今日引语"),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="生成前端站点主题配置")
    ap.add_argument("--check", action="store_true", help="仅校验现有文件是否与 theme.json 一致")
    args = ap.parse_args()

    theme = json.loads(THEME.read_text(encoding="utf-8"))
    config = build_config(theme)
    json_body = json.dumps(config, ensure_ascii=False, indent=2)
    content = (
        "// 站点主题配置：由 tooling/scripts/build_site_config.py 从根目录 theme.json 生成。\n"
        "// 网页与分享海报的所有主题文案都从这里取，换学科 = 换 theme.json + 重跑生成脚本。\n"
        "// 注意：此文件是**生成产物**（勿手改），CI 通过 --check 校验它与 theme.json 的一致性。\n\n"
        "export type SiteConfig = {\n"
        "  name: string;\n"
        "  nameEn: string;\n"
        "  unitLabel: string;\n"
        "  description: string;\n"
        "  origin: string;\n"
        "  basePath: string;\n"
        "  entryRouteSegment: string;\n"
        "  icsFilename: string;\n"
        "  dailyPdfPattern: string;\n"
        "  monthlyPdfFilename: string;\n"
        "  posterSlogan: string;\n"
        "  posterSiteTag: string;\n"
        "  fields: string[];\n"
        "  fallbackEntryId: string;\n"
        "  illustrations: Record<string, string>;\n"
        "  labels: { cardA: string; cardB: string; quoteLabel: string };\n"
        "  heroEyebrow: string;\n"
        "  heroTitle: string;\n"
        "  heroText: string;\n"
        "  heroDiscSuffix: string;\n"
        "  fieldCountLabel: string;\n"
        "  entryCountLabel: string;\n"
        "  monthTip: string;\n"
        "  monthTitle: string;\n"
        "  monthSectionLabel: string;\n"
        "  exploreTitle: string;\n"
        "  searchPlaceholder: string;\n"
        "  searchAriaLabel: string;\n"
        "  filterAriaLabel: string;\n"
        "  manifestoEyebrow: string;\n"
        "  manifestoHtml: string;\n"
        "  manifestoSub: string;\n"
        "  emptySearchTip: string;\n"
        "  archiveEyebrowPrefix: string;\n"
        "  entryIndexPrefix: string;\n"
        "  entryIndexSuffix: string;\n"
        "  footerSummaryPattern: string;\n"
        "};\n\n"
        f"export const SITE_CONFIG: SiteConfig = {json_body};\n\n"
        "/** 全站唯一首页标题（layout + page 共用）。 */\n"
        'export function homeTitle(): string {\n'
        '  return `${SITE_CONFIG.name}｜${SITE_CONFIG.unitLabel.replace(/^位/, "每天认识一位")}`;\n'
        "}\n\n"
        "/** 人物详情页标题。 */\n"
        'export function entryTitle(entryName: string): string {\n'
        '  return `${entryName}｜${SITE_CONFIG.name}`;\n'
        "}\n\n"
        "/** 每日版 PDF 文件名（从数据推导数量）。 */\n"
        'export function dailyPdfFilename(count: number): string {\n'
        '  return SITE_CONFIG.dailyPdfPattern.replace("{count}", String(count));\n'
        "}\n"
    )

    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != content:
            print("✗ src/domain/siteConfig.ts 与 theme.json 不一致，请运行 npm run build:site-config", file=sys.stderr)
            return 1
        print("✓ siteConfig.ts 与 theme.json 一致")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(content, encoding="utf-8")
    print(f"✓ 已生成 {OUT.relative_to(ROOT)}（主题：{config['name']}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
