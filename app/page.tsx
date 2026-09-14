"use client";

import { useEffect, useMemo, useState } from "react";
import scientistsData from "./data/scientists-index.json";
import avatarsData from "../public/avatars.json";
import {
  type ScientistSummary,
  type Field,
  type DateParts,
  getScientistForDate,
} from "../src/domain/calendar";
import { useCurrentDate } from "../src/hooks/useCurrentDate";
import { SITE_BASE_PATH, SITE_URL, scientistAbsoluteUrl, scientistBrowserPath, scientistIdFromPath } from "../src/domain/scientistRoutes";

type AvatarMode = "letter" | "photo";
type ScientistDetail = { story: string; fact: string; quote?: string; quoteSource?: string };
type ScientistSource = { title: string; publisher: string; url: string; covers: string[]; notes?: string };
type ScientistSourceFile = { scientists: Record<string, ScientistSource[]> };
type MonthDetails = Record<string, ScientistDetail>;

const scientists = scientistsData as ScientistSummary[];
const avatars = avatarsData as Record<string, { photo: boolean }>;
const runtimeBasePath = typeof window !== "undefined" && (window.location.pathname === SITE_BASE_PATH || window.location.pathname.startsWith(`${SITE_BASE_PATH}/`))
  ? SITE_BASE_PATH
  : "";
function assetPath(path: string): string {
  return `${runtimeBasePath}/${path.replace(/^\/+/, "")}`;
}
const einsteinIllustration = assetPath("art/einstein-archive.webp");

// 日期与“当前日期”逻辑已移至 src/domain/calendar.ts 与 src/hooks/useCurrentDate.ts

function avatarFor(scientist: ScientistSummary, mode: AvatarMode): string | null {
  if (mode !== "photo") return null;
  if (avatars[scientist.id]?.photo) return assetPath(`avatars/${scientist.id}.jpg`);
  if (scientist.id === "einstein") return einsteinIllustration;
  return null;
}

function hasAlternatePortrait(scientist: ScientistSummary): boolean {
  return Boolean(avatars[scientist.id]?.photo) || scientist.id === "einstein";
}

function alternatePortraitLabel(scientist: ScientistSummary): "照片" | "插画" {
  return avatars[scientist.id]?.photo ? "照片" : "插画";
}

const fields: Array<Field | "全部"> = ["全部", "物理", "化学", "生命科学", "数学", "计算机", "天文", "医学", "地球科学"];
const monthNames = ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"];
const weekdayNames = ["日", "一", "二", "三", "四", "五", "六"];
const ARCHIVE_PAGE_SIZE = 48;
const detailLoaders: Record<number, () => Promise<{ default: MonthDetails }>> = {
  1: () => import("./data/details/01.json"),
  2: () => import("./data/details/02.json"),
  3: () => import("./data/details/03.json"),
  4: () => import("./data/details/04.json"),
  5: () => import("./data/details/05.json"),
  6: () => import("./data/details/06.json"),
  7: () => import("./data/details/07.json"),
  8: () => import("./data/details/08.json"),
  9: () => import("./data/details/09.json"),
  10: () => import("./data/details/10.json"),
  11: () => import("./data/details/11.json"),
  12: () => import("./data/details/12.json"),
};

function formatDate(month: number, day: number) {
  return `${month} 月 ${day} 日`;
}

const HOME_TITLE = "科学家日历｜每天认识一位科学家";
const HOME_DESCRIPTION = "一份写给好奇心的科学日历：每天认识一位科学家、一项发现与一个改变世界的念头。";

function initialScientistRouteId(): string | null {
  if (typeof window === "undefined") return null;
  const routeId = scientistIdFromPath(window.location.pathname);
  return routeId && scientists.some((scientist) => scientist.id === routeId) ? routeId : null;
}

function scientistDescription(scientist: ScientistSummary): string {
  const description = `${scientist.name}（${scientist.latinName}）｜${scientist.country} · ${scientist.field}｜${scientist.tagline}。核心贡献：${scientist.contribution}`;
  return description.length > 170 ? `${description.slice(0, 167)}…` : description;
}

function updateMeta(selector: string, content: string) {
  document.querySelector<HTMLMetaElement>(selector)?.setAttribute("content", content);
}

function applyPageMetadata(scientist: ScientistSummary | null) {
  const title = scientist ? `${scientist.name}｜科学家日历` : HOME_TITLE;
  const description = scientist ? scientistDescription(scientist) : HOME_DESCRIPTION;
  const url = scientist ? scientistAbsoluteUrl(scientist.id) : SITE_URL;
  document.title = title;
  updateMeta('meta[name="description"]', description);
  updateMeta('meta[property="og:title"]', title);
  updateMeta('meta[property="og:description"]', description);
  updateMeta('meta[property="og:url"]', url);
  updateMeta('meta[property="og:type"]', scientist ? "profile" : "website");
  updateMeta('meta[name="twitter:title"]', title);
  updateMeta('meta[name="twitter:description"]', description);
  document.querySelector<HTMLLinkElement>('link[rel="canonical"]')?.setAttribute("href", url);
}

function Calendar({ now }: { now: DateParts }) {
  // 2/29 等闰年专属日期在平年日历无对应人物，已由 getScientistForDate 统一回退到 2/28，
  // 禁止 silent fallback 到 Einstein / 错误月份。
  const todayScientist = getScientistForDate(scientists, now);
  const [activeField, setActiveField] = useState<Field | "全部">("全部");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState(() => initialScientistRouteId() ?? todayScientist?.id ?? "einstein");
  const [profileRouteId, setProfileRouteId] = useState<string | null>(() => initialScientistRouteId());
  // 月历默认停在“当前月份”，不依赖今日人物是否存在（否则 2/29 会错误跳到 7 月）。
  const [calendarMonth, setCalendarMonth] = useState(now.month);
  const [avatarMode, setAvatarMode] = useState<AvatarMode>("letter");
  const [archiveLimit, setArchiveLimit] = useState(ARCHIVE_PAGE_SIZE);
  const [detailsById, setDetailsById] = useState<MonthDetails>({});
  const [detailLoadErrors, setDetailLoadErrors] = useState<Set<number>>(() => new Set());
  const [detailRetryToken, setDetailRetryToken] = useState(0);
  const [shareNotice, setShareNotice] = useState("");
  const [sourceRegistry, setSourceRegistry] = useState<Record<string, ScientistSource[]> | null>(null);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [sourceLoadFailed, setSourceLoadFailed] = useState(false);

  const selected = scientists.find((scientist) => scientist.id === selectedId) ?? scientists[0];
  const selectedDetail = detailsById[selected.id];
  const selectedQuote = selectedDetail?.quote && selectedDetail.quoteSource ? { text: selectedDetail.quote, source: selectedDetail.quoteSource } : undefined;
  const isTodaySelection = selected.id === todayScientist?.id;
  const detailLoadFailed = detailLoadErrors.has(selected.month);

  useEffect(() => {
    applyPageMetadata(profileRouteId === selected.id ? selected : null);
  }, [profileRouteId, selected]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const routeId = scientistIdFromPath(window.location.pathname);
    if (routeId) {
      const frame = window.requestAnimationFrame(() => {
        document.getElementById("today")?.scrollIntoView({ block: "start" });
      });
      return () => window.cancelAnimationFrame(frame);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const handlePopState = () => {
      const routeId = scientistIdFromPath(window.location.pathname);
      const target = routeId ? scientists.find((scientist) => scientist.id === routeId) : todayScientist;
      if (!target) return;
      setProfileRouteId(routeId && target.id === routeId ? routeId : null);
      setSelectedId(target.id);
      setCalendarMonth(target.month);
      setShareNotice("");
      setSourcesOpen(false);
      setSourceLoadFailed(false);
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [todayScientist]);

  useEffect(() => {
    if (detailsById[selected.id]) return;
    let cancelled = false;
    void detailLoaders[selected.month]().then((module) => {
      if (!cancelled) {
        setDetailsById((current) => ({ ...current, ...(module.default as MonthDetails) }));
        setDetailLoadErrors((current) => {
          if (!current.has(selected.month)) return current;
          const next = new Set(current);
          next.delete(selected.month);
          return next;
        });
      }
    }).catch(() => {
      if (!cancelled) {
        setDetailLoadErrors((current) => new Set(current).add(selected.month));
      }
    });
    return () => { cancelled = true; };
  }, [selected.id, selected.month, detailsById, detailRetryToken]);
  const filtered = useMemo(() => scientists.filter((scientist) => {
    const inField = activeField === "全部" || scientist.field === activeField;
    const needle = query.trim().toLowerCase();
    const inSearch = !needle || [scientist.name, scientist.latinName, scientist.field, scientist.country, scientist.contribution].join(" ").toLowerCase().includes(needle);
    return inField && inSearch;
  }), [activeField, query]);
  const visibleScientists = filtered.slice(0, archiveLimit);

  const monthDays = new Date(now.year, calendarMonth, 0).getDate();
  const firstWeekday = new Date(now.year, calendarMonth - 1, 1).getDay();
  const monthEntries = scientists.filter((scientist) => scientist.month === calendarMonth);
  const monthEntriesByDay = new Map<number, ScientistSummary[]>();
  for (const entry of monthEntries) {
    const list = monthEntriesByDay.get(entry.day) ?? [];
    list.push(entry);
    monthEntriesByDay.set(entry.day, list);
  }
  const coveredDays = new Set(scientists.map((scientist) => `${scientist.month}-${scientist.day}`)).size;
  const coveragePercent = Math.min(100, (coveredDays / 365) * 100);

  function selectScientist(scientist: ScientistSummary) {
    if (typeof window !== "undefined") {
      const path = scientistBrowserPath(scientist.id, window.location.pathname);
      if (window.location.pathname !== path) window.history.pushState({ scientistId: scientist.id }, "", path);
    }
    setProfileRouteId(scientist.id);
    setSelectedId(scientist.id);
    setCalendarMonth(scientist.month);
    setShareNotice("");
    setSourcesOpen(false);
    setSourceLoadFailed(false);
    document.getElementById("today")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function cycleDayScientist(day: number) {
    const dayEntries = monthEntriesByDay.get(day) ?? [];
    if (!dayEntries.length) return;
    const currentIndex = dayEntries.findIndex((e) => e.id === selected.id);
    const next = dayEntries[(currentIndex + 1) % dayEntries.length];
    selectScientist(next);
  }

  async function toggleSources() {
  if (sourcesOpen) {
    setSourcesOpen(false);
    return;
  }
  setSourceLoadFailed(false);
  if (!sourceRegistry) {
    try {
      const sourceData = await import("./data/scientist-sources.json");
      setSourceRegistry((sourceData.default as ScientistSourceFile).scientists);
    } catch {
      setSourceLoadFailed(true);
    }
  }
  setSourcesOpen(true);
}

  async function shareSelectedScientist() {
    const url = scientistAbsoluteUrl(selected.id);
    const data = {
      title: `${selected.name}｜科学家日历`,
      text: `认识 ${selected.name}：${selected.tagline}`,
      url,
    };
    try {
      if (navigator.share) {
        await navigator.share(data);
        setShareNotice("已打开系统分享");
        return;
      }
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url);
        setShareNotice("人物链接已复制");
        return;
      }
      window.prompt("复制人物链接", url);
      setShareNotice("可复制上方人物链接");
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setShareNotice("分享失败，请复制地址栏链接");
    }
  }

  return (
    <main>
      <a className="skip-link" href="#today">跳到今日人物</a>
      <nav className="site-nav" aria-label="主导航">
        <a className="brand" href="#top" aria-label="科学家日历首页"><span className="brand-mark">∴</span> 科学家日历</a>
        <div className="nav-links"><a href="#calendar">日历</a><a href="#explore">探索</a><a href="#about">关于</a></div>
        <a className="nav-action" href="#explore">开始探索 <span>↗</span></a>
      </nav>

      <section className="hero" id="top" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="eyebrow">THE DAILY SCIENCE NOTEBOOK · {now.year}</p>
          <h1 id="hero-title">每天，<br /><em>遇见一个</em><br />改变世界的念头。</h1>
          <p className="hero-text">一份写给好奇心的科学日历。从一位科学家、一项发现，走进人类理解世界的方式。</p>
          <div className="hero-actions">
          <a className="button-primary" href="#today">阅读今日人物 <span>↓</span></a>
          <a className="button-secondary" href="#calendar">查看月历 <span>→</span></a>
          <details className="print-menu">
            <summary>打印版 <span>↓</span></summary>
            <div className="print-menu-panel">
              <a href={assetPath(`print/科学家日历_精选${scientists.length}位_A4打印版.pdf`)} download><strong>每日人物版</strong><small>{scientists.length} 位 · A4 横版</small></a>
              <a href={assetPath("print/科学家日历_月度生日版_A4.pdf")} download><strong>月度生日版</strong><small>生日 · 名字 · 名言</small></a>
            </div>
          </details>
        </div>
        </div>
        <div className="orbit-art" aria-hidden="true">
          <div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="orbit orbit-three" />
          <div className="star star-a" /> <div className="star star-b" /> <div className="star star-c" />
          <div className="hero-disc"><span>365</span><small>种好奇</small></div>
          <p className="art-caption">每一个答案<br />都从一个问题开始</p>
        </div>
      </section>

      <section className="overview-strip" aria-label="日历内容概览">
        <div><strong>{scientists.length}</strong><span>位人物档案</span></div>
        <div><strong>{fields.length - 1}</strong><span>个科学领域</span></div>
        <div><strong>{coveredDays}</strong><span>个已覆盖日期</span></div>
        <p className="coverage-note">全年覆盖进度 <strong>{coveredDays} / 365</strong><span className="coverage-bar"><i style={{ width: `${coveragePercent}%` }} /></span></p>
      </section>

      <section className="today-section" id="today" aria-labelledby="today-title">
        <header className="section-heading"><div><p className="eyebrow">{isTodaySelection ? "TODAY&apos;S NOTE" : "ARCHIVE NOTE"} · {formatDate(selected.month, selected.day)}</p><h2 id="today-title">{isTodaySelection ? "今日人物" : "人物档案"}</h2></div><p className="section-aside">第 {String(selected.month).padStart(2, "0")}.{String(selected.day).padStart(2, "0")} 页 / 365</p></header>
        <article className={`feature-card tone-${selected.color}`}>
          <div className="portrait-panel"><span className="portrait-number">{String(selected.month).padStart(2, "0")}.{String(selected.day).padStart(2, "0")}</span>{(() => { const src = avatarFor(selected, avatarMode); if (src) return <img className={`portrait-image mode-${avatarMode}`} src={src} alt={`${selected.name}的${alternatePortraitLabel(selected)}肖像`} loading="lazy" />; return <div className={`portrait-abstract tone-${selected.color}`} aria-hidden="true"><i /><b>{selected.name.slice(0, 1)}</b><em>{selected.latinName}</em></div>; })()}<span className="portrait-field">{selected.field}</span>
            {hasAlternatePortrait(selected) && <div className="portrait-switch" role="group" aria-label="头像模式">
    <button type="button" className={avatarMode === "letter" ? "active" : ""} aria-pressed={avatarMode === "letter"} onClick={() => setAvatarMode("letter")}>单字</button>
    <button type="button" className={avatarMode === "photo" ? "active" : ""} aria-pressed={avatarMode === "photo"} onClick={() => setAvatarMode("photo")}>{alternatePortraitLabel(selected)}</button>
  </div>}
          </div>
          <div className="feature-copy"><p className="feature-relation">{selected.relation} · {selected.years}</p><h3>{selected.name}</h3><p className="latin-name">{selected.latinName} · {selected.country}</p><p className="feature-tagline">阅读线索｜{selected.tagline}</p>{selectedQuote && <blockquote className="quote-block"><span>{isTodaySelection ? "今日引语" : "人物引语"}</span><p>“{selectedQuote.text}”</p><cite>— {selectedQuote.source}</cite></blockquote>}<p className="feature-story" aria-live="polite">{selectedDetail?.story ?? (detailLoadFailed ? "人物档案加载失败，请检查网络后重试。" : "正在加载人物档案…")}</p><div className="feature-meta"><div><span>核心贡献</span><strong>{selected.contribution}</strong></div><div><span>你知道吗</span><strong>{selectedDetail?.fact ?? (detailLoadFailed ? "暂时无法加载" : "正在加载…")}</strong></div></div>{detailLoadFailed && <button className="retry-button" type="button" onClick={() => { setDetailLoadErrors((current) => { const next = new Set(current); next.delete(selected.month); return next; }); setDetailRetryToken((token) => token + 1); }}>重新加载人物档案 <span>↻</span></button>}<div className="feature-utilities" aria-label="人物辅助操作"><button className="utility-button" type="button" onClick={() => { void shareSelectedScientist(); }}>分享 <span>↗</span></button><button className="utility-button" type="button" aria-expanded={sourcesOpen} onClick={() => { void toggleSources(); }}>资料来源 <span>{sourcesOpen ? "−" : "+"}</span></button>{shareNotice && <span className="share-notice" role="status" aria-live="polite">{shareNotice}</span>}</div>{sourcesOpen && <div className="source-panel" aria-live="polite">{sourceLoadFailed ? <p>资料来源暂时无法加载，请稍后重试。</p> : sourceRegistry?.[selected.id]?.length ? <ul>{sourceRegistry[selected.id].map((source) => <li key={source.url}><a href={source.url} target="_blank" rel="noreferrer"><strong>{source.publisher}</strong><span>{source.title}</span></a></li>)}</ul> : <p>该人物的资料来源正在逐步补齐。</p>}</div>}<button className="feature-continue" type="button" onClick={() => document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" })}>继续探索档案库 <span>→</span></button></div>
          <div className="feature-index" aria-hidden="true"><span>SCIENCE</span><span>NOTE</span><b>{selected.id.slice(0, 3).toUpperCase()}</b></div>
        </article>
      </section>

      <section className="calendar-section" id="calendar" aria-labelledby="calendar-title">
        <header className="section-heading"><div><p className="eyebrow">SCIENCE DATES · {now.year}</p><h2 id="calendar-title">月历</h2></div><div className="month-switcher"><button type="button" aria-label="上一个月" onClick={() => setCalendarMonth((month) => month === 1 ? 12 : month - 1)}>←</button><span>{monthNames[calendarMonth - 1]} {now.year}</span><button type="button" aria-label="下一个月" onClick={() => setCalendarMonth((month) => month === 12 ? 1 : month + 1)}>→</button></div></header>
        <div className="calendar-layout"><div className="calendar-grid" role="grid" aria-label={`${calendarMonth} 月日历`}><div className="weekdays">{weekdayNames.map((day) => <span key={day}>{day}</span>)}</div><div className="dates">{Array.from({ length: firstWeekday }, (_, index) => <span className="blank-day" key={`blank-${index}`} />)}{Array.from({ length: monthDays }, (_, index) => { const day = index + 1; const dayEntries = monthEntriesByDay.get(day) ?? []; return <button className={`date-cell ${dayEntries.length ? `has-entry ${dayEntries.some((e) => e.id === selected.id) ? "selected" : ""}` : ""}`} type="button" key={day} onClick={() => dayEntries.length && (dayEntries.length > 1 ? cycleDayScientist(day) : selectScientist(dayEntries[0]))} disabled={!dayEntries.length} title={dayEntries.length ? `${day} 日：${dayEntries.map((e) => e.name).join("、")}${dayEntries.length > 1 ? "（点击切换）" : ""}` : undefined} aria-label={dayEntries.length ? `${day} 日：${dayEntries.map((e) => e.name).join("、")}` : `${day} 日没有收录人物`}><span>{day}</span>{dayEntries.length > 0 && <span className="dots" aria-hidden="true">{dayEntries.map((entry) => <i key={entry.id} className={`dot ${entry.color}${entry.id === selected.id ? " active" : ""}`} />)}</span>}</button>; })}</div></div>
          <aside className="calendar-notes"><p className="eyebrow">THIS MONTH</p><h3>{monthEntries.length ? `${monthEntries.length} 个科学瞬间` : "正在整理中"}</h3>{monthEntries.length ? monthEntries.map((entry) => <button className="month-entry" type="button" key={entry.id} onClick={() => selectScientist(entry)}><span>{String(entry.day).padStart(2, "0")}</span><div><strong>{entry.name}</strong><small>{entry.relation} · {entry.field}</small></div><b>↗</b></button>) : <p>这一页将留给新的好奇心。</p>}<p className="calendar-tip">带有彩色圆点的日期收录了科学人物；同一天多位人物时，点击日期可切换查看，圆点高亮为当前人物。</p></aside></div>
      </section>

      <section className="explore-section" id="explore" aria-labelledby="explore-title">
        <header className="section-heading explore-heading"><div><p className="eyebrow">THE ARCHIVE · {scientists.length} STARTING POINTS</p><h2 id="explore-title">从好奇出发</h2></div><label className="search-box"><span>⌕</span><input value={query} onChange={(event) => { setQuery(event.target.value); setArchiveLimit(ARCHIVE_PAGE_SIZE); }} placeholder="搜索人物、领域或贡献" aria-label="搜索科学家档案" /></label></header>
        <div className="field-filters" aria-label="按科学领域筛选">{fields.map((field) => <button key={field} type="button" className={field === activeField ? "active" : ""} onClick={() => { setActiveField(field); setArchiveLimit(ARCHIVE_PAGE_SIZE); }}>{field}</button>)}</div>
        <div className="archive-toolbar" aria-live="polite"><p>当前显示 <strong>{filtered.length}</strong> / {scientists.length} 位人物{activeField !== "全部" ? ` · ${activeField}` : ""}{query.trim() ? ` · “${query.trim()}”` : ""}</p>{(activeField !== "全部" || query) && <button type="button" onClick={() => { setActiveField("全部"); setQuery(""); setArchiveLimit(ARCHIVE_PAGE_SIZE); }}>清除筛选</button>}</div>
        <div className="archive-grid">{visibleScientists.map((scientist, index) => <button className={`archive-card tone-${scientist.color}`} type="button" key={scientist.id} aria-label={`阅读 ${scientist.name} 的人物档案`} onClick={() => selectScientist(scientist)}><span className="archive-date">{String(scientist.month).padStart(2, "0")}.{String(scientist.day).padStart(2, "0")}</span>{(() => { const src = avatarFor(scientist, avatarMode); if (src) return <img className="archive-art archive-photo" src={src} alt="" loading="lazy" />; return <span className="archive-art" aria-hidden="true"><i /><b>{scientist.name.slice(0, 1)}</b><em>{scientist.field}</em></span>; })()}<span className="archive-field">{scientist.field}</span><h3>{scientist.name}</h3><p>{scientist.tagline}</p><span className="archive-open">阅读档案 <b>↗</b></span><i className="archive-index">{String(index + 1).padStart(2, "0")}</i></button>)}</div>
        {visibleScientists.length < filtered.length && <button className="button-secondary" type="button" onClick={() => setArchiveLimit((limit) => Math.min(limit + ARCHIVE_PAGE_SIZE, filtered.length))}>加载更多 · 还剩 {filtered.length - visibleScientists.length} 位 <span>↓</span></button>}
        {!filtered.length && <p className="empty-state">没有找到匹配的人物。换个关键词试试。</p>}
      </section>

      <section className="manifesto" id="about"><p className="eyebrow">WHY A SCIENCE CALENDAR</p><p>科学并非一串遥远的姓名与年份，<br />而是一代代人对世界的<strong>耐心注视</strong>。</p><span>收藏今天的好奇，明天继续提问。</span></section>

      <footer><a className="brand" href="#top"><span className="brand-mark">∴</span> 科学家日历</a><p>精选 {scientists.length} 位人物档案 · 持续更新中</p><a className="footer-download" href={assetPath(`print/科学家日历_精选${scientists.length}位_A4打印版.pdf`)} download>下载 A4 打印版 ↓</a><a href="#top">回到顶部 ↑</a></footer>
    </main>
  );
}

export default function Home() {
  // useCurrentDate：SSR 用 UTC 保证水合一致，客户端挂载后切本地时间，
  // 并精确调度到下一次本地午夜 + visibilitychange 回到前台时刷新，跨午夜无需手动刷新。
  const now = useCurrentDate();
  return <Calendar key={`${now.year}-${now.month}-${now.day}`} now={now} />;
}
