"use client";

import { useMemo, useState } from "react";
import quotes from "./quotes.json";
import scientistsData from "./scientists.json";

type Field = "物理" | "化学" | "生命科学" | "数学" | "计算机" | "天文" | "医学" | "地球科学";

type Scientist = {
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
  story: string;
  contribution: string;
  fact: string;
  quote?: string;
  quoteSource?: string;
};

const scientists = scientistsData as Scientist[];

const fields: Array<Field | "全部"> = ["全部", "物理", "化学", "生命科学", "数学", "计算机", "天文", "医学", "地球科学"];
const monthNames = ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"];
const weekdayNames = ["日", "一", "二", "三", "四", "五", "六"];

function formatDate(month: number, day: number) {
  return `${month} 月 ${day} 日`;
}

export default function Home() {
  const [activeField, setActiveField] = useState<Field | "全部">("全部");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState("einstein");
  const [calendarMonth, setCalendarMonth] = useState(7);

  const selected = scientists.find((scientist) => scientist.id === selectedId) ?? scientists[0];
  const selectedQuote = quotes[selected.id as keyof typeof quotes] ?? (selected.quote ? { text: selected.quote, source: selected.quoteSource ?? "编者整理" } : undefined);
  const filtered = useMemo(() => scientists.filter((scientist) => {
    const inField = activeField === "全部" || scientist.field === activeField;
    const needle = query.trim().toLowerCase();
    const inSearch = !needle || [scientist.name, scientist.latinName, scientist.field, scientist.country, scientist.contribution].join(" ").toLowerCase().includes(needle);
    return inField && inSearch;
  }), [activeField, query]);

  const monthDays = new Date(2026, calendarMonth, 0).getDate();
  const firstWeekday = new Date(2026, calendarMonth - 1, 1).getDay();
  const monthEntries = scientists.filter((scientist) => scientist.month === calendarMonth);
  const coveredDays = new Set(scientists.map((scientist) => `${scientist.month}-${scientist.day}`)).size;
  const coveragePercent = Math.min(100, (coveredDays / 365) * 100);

  function selectScientist(scientist: Scientist) {
    setSelectedId(scientist.id);
    setCalendarMonth(scientist.month);
    document.getElementById("today")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <main>
      <nav className="site-nav" aria-label="主导航">
        <a className="brand" href="#top" aria-label="科学家日历首页"><span className="brand-mark">∴</span> 科学家日历</a>
        <div className="nav-links"><a href="#calendar">日历</a><a href="#explore">探索</a><a href="#about">关于</a></div>
        <a className="nav-action" href="#explore">开始探索 <span>↗</span></a>
      </nav>

      <section className="hero" id="top" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="eyebrow">THE DAILY SCIENCE NOTEBOOK · 2026</p>
          <h1 id="hero-title">每天，<br /><em>遇见一个</em><br />改变世界的念头。</h1>
          <p className="hero-text">一份写给好奇心的科学日历。从一位科学家、一项发现，走进人类理解世界的方式。</p>
          <div className="hero-actions"><a className="button-primary" href="#today">阅读今日人物 <span>↓</span></a><a className="button-secondary" href={`print/科学家日历_精选${scientists.length}位_A4打印版.pdf`} download>获取 A4 打印版 <span>↓</span></a><a className="text-link" href="#calendar">查看月历 <span>→</span></a></div>
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
        <header className="section-heading"><div><p className="eyebrow">TODAY&apos;S NOTE · {formatDate(selected.month, selected.day)}</p><h2 id="today-title">今日人物</h2></div><p className="section-aside">第 {String(selected.month).padStart(2, "0")}.{String(selected.day).padStart(2, "0")} 页 / 365</p></header>
        <article className={`feature-card tone-${selected.color}`}>
          <div className="portrait-panel"><span className="portrait-number">{String(selected.month).padStart(2, "0")}.{String(selected.day).padStart(2, "0")}</span>{selected.id === "einstein" ? <img className="portrait-illustration" src="art/einstein-archive.webp" alt="阿尔伯特·爱因斯坦的复古科学插画肖像" /> : <div className={`portrait-abstract tone-${selected.color}`} aria-hidden="true"><i /><b>{selected.name.slice(0, 1)}</b><em>{selected.latinName}</em></div>}<span className="portrait-field">{selected.field}</span></div>
          <div className="feature-copy"><p className="feature-relation">{selected.relation} · {selected.years}</p><h3>{selected.name}</h3><p className="latin-name">{selected.latinName} · {selected.country}</p><p className="feature-tagline">“{selected.tagline}”</p>{selectedQuote && <blockquote className="quote-block"><span>今日引语</span><p>“{selectedQuote.text}”</p><cite>— {selectedQuote.source}</cite></blockquote>}<p className="feature-story">{selected.story}</p><div className="feature-meta"><div><span>核心贡献</span><strong>{selected.contribution}</strong></div><div><span>你知道吗</span><strong>{selected.fact}</strong></div></div><button className="detail-button" type="button" onClick={() => document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" })}>在档案库中继续探索 <span>→</span></button></div>
          <div className="feature-index" aria-hidden="true"><span>SCIENCE</span><span>NOTE</span><b>{selected.id.slice(0, 3).toUpperCase()}</b></div>
        </article>
      </section>

      <section className="calendar-section" id="calendar" aria-labelledby="calendar-title">
        <header className="section-heading"><div><p className="eyebrow">SCIENCE DATES · 2026</p><h2 id="calendar-title">月历</h2></div><div className="month-switcher"><button type="button" aria-label="上一个月" onClick={() => setCalendarMonth((month) => month === 1 ? 12 : month - 1)}>←</button><span>{monthNames[calendarMonth - 1]} 2026</span><button type="button" aria-label="下一个月" onClick={() => setCalendarMonth((month) => month === 12 ? 1 : month + 1)}>→</button></div></header>
        <div className="calendar-layout"><div className="calendar-grid" role="grid" aria-label={`${calendarMonth} 月日历`}><div className="weekdays">{weekdayNames.map((day) => <span key={day}>{day}</span>)}</div><div className="dates">{Array.from({ length: firstWeekday }, (_, index) => <span className="blank-day" key={`blank-${index}`} />)}{Array.from({ length: monthDays }, (_, index) => { const day = index + 1; const entry = monthEntries.find((scientist) => scientist.day === day); return <button className={`date-cell ${entry ? `has-entry ${entry.id === selected.id ? "selected" : ""}` : ""}`} type="button" key={day} onClick={() => entry && selectScientist(entry)} disabled={!entry} aria-label={entry ? `${day} 日：${entry.name}` : `${day} 日没有收录人物`}><span>{day}</span>{entry && <i className={`dot ${entry.color}`} />}</button>; })}</div></div>
          <aside className="calendar-notes"><p className="eyebrow">THIS MONTH</p><h3>{monthEntries.length ? `${monthEntries.length} 个科学瞬间` : "正在整理中"}</h3>{monthEntries.length ? monthEntries.map((entry) => <button className="month-entry" type="button" key={entry.id} onClick={() => selectScientist(entry)}><span>{String(entry.day).padStart(2, "0")}</span><div><strong>{entry.name}</strong><small>{entry.relation} · {entry.field}</small></div><b>↗</b></button>) : <p>这一页将留给新的好奇心。</p>}<p className="calendar-tip">带有彩色圆点的日期，收录了一则科学人物或科学史纪念。</p></aside></div>
      </section>

      <section className="explore-section" id="explore" aria-labelledby="explore-title">
        <header className="section-heading explore-heading"><div><p className="eyebrow">THE ARCHIVE · {scientists.length} STARTING POINTS</p><h2 id="explore-title">从好奇出发</h2></div><label className="search-box"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索人物、领域或贡献" aria-label="搜索科学家档案" /></label></header>
        <div className="field-filters" aria-label="按科学领域筛选">{fields.map((field) => <button key={field} type="button" className={field === activeField ? "active" : ""} onClick={() => setActiveField(field)}>{field}</button>)}</div>
        <div className="archive-toolbar" aria-live="polite"><p>当前显示 <strong>{filtered.length}</strong> / {scientists.length} 位人物{activeField !== "全部" ? ` · ${activeField}` : ""}{query.trim() ? ` · “${query.trim()}”` : ""}</p>{(activeField !== "全部" || query) && <button type="button" onClick={() => { setActiveField("全部"); setQuery(""); }}>清除筛选</button>}</div>
        <div className="archive-grid">{filtered.map((scientist, index) => <button className={`archive-card tone-${scientist.color}`} type="button" key={scientist.id} onClick={() => selectScientist(scientist)}><span className="archive-date">{String(scientist.month).padStart(2, "0")}.{String(scientist.day).padStart(2, "0")}</span><span className="archive-art" aria-hidden="true"><i /><b>{scientist.name.slice(0, 1)}</b><em>{scientist.field}</em></span><span className="archive-field">{scientist.field}</span><h3>{scientist.name}</h3><p>{scientist.tagline}</p><span className="archive-open">阅读档案 <b>↗</b></span><i className="archive-index">{String(index + 1).padStart(2, "0")}</i></button>)}</div>
        {!filtered.length && <p className="empty-state">没有找到匹配的人物。换个关键词试试。</p>}
      </section>

      <section className="manifesto" id="about"><p className="eyebrow">WHY A SCIENCE CALENDAR</p><p>科学并非一串遥远的姓名与年份，<br />而是一代代人对世界的<strong>耐心注视</strong>。</p><span>收藏今天的好奇，明天继续提问。</span></section>

      <footer><a className="brand" href="#top"><span className="brand-mark">∴</span> 科学家日历</a><p>精选 {scientists.length} 位人物档案 · 持续更新中</p><a className="footer-download" href={`print/科学家日历_精选${scientists.length}位_A4打印版.pdf`} download>下载 A4 打印版 ↓</a><a href="#top">回到顶部 ↑</a></footer>
    </main>
  );
}
