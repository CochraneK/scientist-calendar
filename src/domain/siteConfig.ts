// 站点主题配置：由 tooling/scripts/build_site_config.py 从根目录 theme.json 生成。
// 网页与分享海报的所有主题文案都从这里取，换学科 = 换 theme.json + 重跑生成脚本。
// 注意：此文件是**生成产物**（勿手改），CI 通过 --check 校验它与 theme.json 的一致性。

export type SiteConfig = {
  name: string;
  nameEn: string;
  unitLabel: string;
  description: string;
  origin: string;
  basePath: string;
  entryRouteSegment: string;
  icsFilename: string;
  dailyPdfPattern: string;
  monthlyPdfFilename: string;
  posterSlogan: string;
  posterSiteTag: string;
  fields: string[];
  fallbackEntryId: string;
  illustrations: Record<string, string>;
  labels: { cardA: string; cardB: string; quoteLabel: string };
  heroEyebrow: string;
  heroTitle: string;
  heroText: string;
  heroDiscSuffix: string;
  fieldCountLabel: string;
  entryCountLabel: string;
  monthTip: string;
  monthTitle: string;
  monthSectionLabel: string;
  exploreTitle: string;
  searchPlaceholder: string;
  searchAriaLabel: string;
  filterAriaLabel: string;
  manifestoEyebrow: string;
  manifestoHtml: string;
  manifestoSub: string;
  emptySearchTip: string;
  archiveEyebrowPrefix: string;
  entryIndexPrefix: string;
  entryIndexSuffix: string;
  footerSummaryPattern: string;
};

export const SITE_CONFIG: SiteConfig = {
  "name": "科学家日历",
  "nameEn": "Scientist Calendar",
  "unitLabel": "位科学家",
  "description": "一份写给好奇心的科学日历：每天认识一位科学家、一项发现与一个改变世界的念头。",
  "origin": "https://cochranek.github.io",
  "basePath": "/scientist-calendar",
  "entryRouteSegment": "scientists",
  "icsFilename": "scientist-calendar.ics",
  "dailyPdfPattern": "科学家日历_精选{count}位_A4打印版.pdf",
  "monthlyPdfFilename": "科学家日历_月度生日版_A4.pdf",
  "posterSlogan": "每天遇见一个改变世界的念头",
  "posterSiteTag": "cochranek.github.io/scientist-calendar",
  "fields": [
    "物理",
    "化学",
    "生命科学",
    "数学",
    "计算机",
    "天文",
    "医学",
    "地球科学"
  ],
  "fallbackEntryId": "einstein",
  "illustrations": {
    "einstein": "art/einstein-archive.webp"
  },
  "heroEyebrow": "THE DAILY SCIENCE NOTEBOOK",
  "heroTitle": "今天，遇见一个改变世界的念头。",
  "heroText": "一份写给好奇心的科学日历。从一位科学家、一项发现，走进人类理解世界的方式。",
  "heroDiscSuffix": "种好奇",
  "fieldCountLabel": "个科学领域",
  "entryCountLabel": "位人物档案",
  "monthTip": "带有彩色圆点的日期收录了科学人物；同一天多位人物时，点击日期可切换查看，圆点高亮为当前人物。",
  "monthTitle": "月历",
  "monthSectionLabel": "个科学瞬间",
  "exploreTitle": "从好奇出发",
  "searchPlaceholder": "搜索人物、领域或贡献",
  "searchAriaLabel": "搜索科学家档案",
  "filterAriaLabel": "按科学领域筛选",
  "manifestoEyebrow": "WHY A SCIENCE CALENDAR",
  "manifestoHtml": "科学并非一串遥远的姓名与年份，<br />而是一代代人对世界的<strong>耐心注视</strong>。",
  "manifestoSub": "收藏今天的好奇，明天继续提问。",
  "emptySearchTip": "没有找到匹配的人物，换个关键词或领域试试。",
  "archiveEyebrowPrefix": "THE ARCHIVE",
  "entryIndexPrefix": "SCIENCE",
  "entryIndexSuffix": "NOTE",
  "footerSummaryPattern": "精选 {count} 位人物档案 · 持续更新中",
  "labels": {
    "cardA": "核心贡献",
    "cardB": "你知道吗",
    "quoteLabel": "今日引语"
  }
};

/** 全站唯一首页标题（layout + page 共用）。 */
export function homeTitle(): string {
  return `${SITE_CONFIG.name}｜${SITE_CONFIG.unitLabel.replace(/^位/, "每天认识一位")}`;
}

/** 人物详情页标题。 */
export function entryTitle(entryName: string): string {
  return `${entryName}｜${SITE_CONFIG.name}`;
}

/** 每日版 PDF 文件名（从数据推导数量）。 */
export function dailyPdfFilename(count: number): string {
  return SITE_CONFIG.dailyPdfPattern.replace("{count}", String(count));
}
