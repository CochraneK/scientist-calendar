// 日期与日历领域逻辑：所有日期业务规则集中在此，组件不再各自推导。
// 同时被 app/page.tsx（Next 主应用）与 tooling/pages（GitHub Pages 静态站）复用。

export type Field =
  | "物理"
  | "化学"
  | "生命科学"
  | "数学"
  | "计算机"
  | "天文"
  | "医学"
  | "地球科学";

export type ScientistSummary = {
  id: string;
  month: number;
  day: number;
  name: string;
  latinName: string;
  years: string;
  field: Field;
  country: string;
  color: string;
  relation: string;
  tagline: string;
  contribution: string;
};

export type Scientist = ScientistSummary & {
  story: string;
  fact: string;
  quote?: string;
  quoteSource?: string;
};

export type DateParts = { year: number; month: number; day: number };

// 平年每月天数（二月 28）——365 天日历的合法日期基准。
const COMMON_YEAR_LENGTHS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

export function getLocalDate(): DateParts {
  const d = new Date();
  return { year: d.getFullYear(), month: d.getMonth() + 1, day: d.getDate() };
}

// SSR / 首屏使用 UTC，保证服务端与客户端的初始渲染一致，避免水合不匹配；
// 客户端挂载后再由 useCurrentDate 切换到本地时间。
export function getUTCDate(): DateParts {
  const d = new Date();
  return { year: d.getUTCFullYear(), month: d.getUTCMonth() + 1, day: d.getUTCDate() };
}

export function getDateKey(month: number, day: number): string {
  return `${month}/${day}`;
}

/**
 * 闰年专属日期（2 月 29 日）在 365 天平年日历中没有对应人物。
 * 统一映射到 2 月 28 日，并显式标记 isLeapDay，禁止任何 silent fallback 到无关人物。
 */
export function resolveCalendarDate(
  date: DateParts,
): { date: DateParts; isLeapDay: boolean } {
  if (date.month === 2 && date.day === 29) {
    return { date: { ...date, month: 2, day: 28 }, isLeapDay: true };
  }
  return { date, isLeapDay: false };
}

export function getDaysInMonth(year: number, month: number): number {
  if (month === 2) {
    const leap = (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
    return leap ? 29 : 28;
  }
  return COMMON_YEAR_LENGTHS[month - 1];
}

/** 按“当日人物”语义取科学家：闰年 2/29 自动回退到 2/28。 */
export function getScientistForDate<T extends { month: number; day: number }>(
  scientists: T[],
  date: DateParts,
): T | undefined {
  const { date: resolved } = resolveCalendarDate(date);
  return scientists.find(
    (s) => s.month === resolved.month && s.day === resolved.day,
  );
}

/** 按 (month*100+day) 聚合，便于“同日多人”快速索引。 */
export function groupScientistsByDate(
  scientists: Scientist[],
): Map<number, Scientist[]> {
  const map = new Map<number, Scientist[]>();
  for (const s of scientists) {
    const key = s.month * 100 + s.day;
    const list = map.get(key) ?? [];
    list.push(s);
    map.set(key, list);
  }
  return map;
}

export function getPreviousMonth(month: number): number {
  return month === 1 ? 12 : month - 1;
}

export function getNextMonth(month: number): number {
  return month === 12 ? 1 : month + 1;
}
