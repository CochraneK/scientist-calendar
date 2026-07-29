"use client";

import { useMemo, useState } from "react";

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
};

const scientists: Scientist[] = [
  { id: "braille", month: 1, day: 4, name: "路易·布莱叶", latinName: "Louis Braille", years: "1809–1852", field: "生命科学", country: "法国", color: "coral", relation: "诞辰", tagline: "让文字可以被指尖阅读", story: "15 岁时，他把军用夜读密码改造成六点触摸书写法。", contribution: "布莱叶盲文", fact: "一格盲文最多由 6 个凸点构成。" },
  { id: "hawking", month: 1, day: 8, name: "史蒂芬·霍金", latinName: "Stephen Hawking", years: "1942–2018", field: "物理", country: "英国", color: "blue", relation: "诞辰", tagline: "把黑洞带进了可计算的宇宙", story: "他提出黑洞并非永远沉默，而会因量子效应缓慢辐射。", contribution: "霍金辐射", fact: "他的科普书《时间简史》曾在英国畅销书榜停留多年。" },
  { id: "franklin", month: 2, day: 4, name: "罗莎琳德·富兰克林", latinName: "Rosalind Franklin", years: "1920–1958", field: "化学", country: "英国", color: "violet", relation: "诞辰", tagline: "用一张衍射照片看见 DNA", story: "她用 X 射线衍射获得了著名的“照片 51”，为理解 DNA 的螺旋结构提供关键线索。", contribution: "DNA 结构研究", fact: "她也对煤、病毒结构做过扎实研究。" },
  { id: "darwin", month: 2, day: 12, name: "查尔斯·达尔文", latinName: "Charles Darwin", years: "1809–1882", field: "生命科学", country: "英国", color: "green", relation: "诞辰", tagline: "让生命拥有一条漫长的时间线", story: "从小猎犬号航行中的观察出发，他提出自然选择解释物种如何改变。", contribution: "进化论", fact: "小猎犬号航行历时近五年。" },
  { id: "galileo", month: 2, day: 15, name: "伽利略·伽利莱", latinName: "Galileo Galilei", years: "1564–1642", field: "天文", country: "意大利", color: "gold", relation: "诞辰", tagline: "用望远镜改变了天空", story: "他观测到木星卫星与金星盈亏，让天体不再只是哲学推论。", contribution: "系统天文观测", fact: "他发现的木星四颗大卫星今天仍以他命名。" },
  { id: "copernicus", month: 2, day: 19, name: "尼古拉·哥白尼", latinName: "Nicolaus Copernicus", years: "1473–1543", field: "天文", country: "波兰", color: "gold", relation: "诞辰", tagline: "让地球离开宇宙的中心", story: "他的日心说将行星的复杂运动放进一个更简洁的秩序。", contribution: "日心说", fact: "他的代表作在临终前后才正式出版。" },
  { id: "einstein", month: 3, day: 14, name: "阿尔伯特·爱因斯坦", latinName: "Albert Einstein", years: "1879–1955", field: "物理", country: "德国", color: "blue", relation: "诞辰", tagline: "重新定义时间、空间与重力", story: "1905 年，他接连发表多篇论文，推动了现代物理的转折。", contribution: "相对论与光电效应", fact: "GPS 的高精度定位需要修正相对论造成的时间差。" },
  { id: "curie", month: 11, day: 7, name: "玛丽·居里", latinName: "Marie Curie", years: "1867–1934", field: "物理", country: "波兰 / 法国", color: "violet", relation: "诞辰", tagline: "在微光里发现两种新元素", story: "她与皮埃尔·居里从沥青铀矿残渣中分离并研究放射性。", contribution: "放射性研究", fact: "她是首位获得诺贝尔奖的女性，也是首位两获诺奖的人。" },
  { id: "lamarr", month: 11, day: 9, name: "海蒂·拉玛", latinName: "Hedy Lamarr", years: "1914–2000", field: "计算机", country: "奥地利 / 美国", color: "coral", relation: "诞辰", tagline: "在银幕之外，构想通信的跳频", story: "她与乔治·安泰尔提出跳频通信构想，为现代无线通信的发展留下重要灵感。", contribution: "跳频通信构想", fact: "她同时是一位知名电影演员与发明者。" },
  { id: "nobel", month: 12, day: 10, name: "诺贝尔奖日", latinName: "Nobel Prize Day", years: "1901–至今", field: "医学", country: "瑞典", color: "gold", relation: "颁奖日", tagline: "让突破被世界看见", story: "诺贝尔奖通常在 12 月 10 日颁发，纪念阿尔弗雷德·诺贝尔逝世日。", contribution: "跨学科科学奖项", fact: "和平奖在奥斯陆颁发，其他奖项在斯德哥尔摩。" },
  { id: "leonardo", month: 4, day: 15, name: "列奥纳多·达·芬奇", latinName: "Leonardo da Vinci", years: "1452–1519", field: "地球科学", country: "意大利", color: "coral", relation: "诞辰", tagline: "把观察变成了跨学科的笔记", story: "从人体解剖到水流、飞行与机械，他用图像记录对自然的好奇。", contribution: "科学观察与工程手稿", fact: "他的手稿常以镜像书写。" },
  { id: "nightingale", month: 5, day: 12, name: "弗洛伦斯·南丁格尔", latinName: "Florence Nightingale", years: "1820–1910", field: "医学", country: "英国", color: "green", relation: "诞辰", tagline: "用数据让医院变得更安全", story: "她将战地医院的死亡原因制成醒目的统计图，推动卫生改革。", contribution: "现代护理与卫生统计", fact: "她的极坐标图是数据可视化史上的经典案例。" },
  { id: "turing", month: 6, day: 23, name: "艾伦·图灵", latinName: "Alan Turing", years: "1912–1954", field: "计算机", country: "英国", color: "blue", relation: "诞辰", tagline: "在纸上发明一台通用计算机", story: "他的抽象计算模型告诉我们：哪些问题能被算法解决，哪些不能。", contribution: "图灵机与计算理论", fact: "图灵测试至今仍是人工智能讨论中的重要概念。" },
  { id: "goeppert", month: 6, day: 28, name: "玛丽亚·格佩特-梅耶", latinName: "Maria Goeppert-Mayer", years: "1906–1972", field: "物理", country: "德国 / 美国", color: "violet", relation: "诞辰", tagline: "解释原子核为何拥有“魔数”", story: "她提出核壳层模型，说明某些核子数为何格外稳定。", contribution: "核壳层模型", fact: "她是第二位获得诺贝尔物理学奖的女性。" },
  { id: "leibniz", month: 7, day: 1, name: "戈特弗里德·莱布尼茨", latinName: "G. W. Leibniz", years: "1646–1716", field: "数学", country: "德国", color: "gold", relation: "诞辰", tagline: "把变化写成一门语言", story: "他与牛顿各自发展微积分，并系统使用了至今常见的积分符号。", contribution: "微积分记号", fact: "二进制思想也曾在他的著作中被清晰阐述。" },
  { id: "bell", month: 7, day: 15, name: "乔斯琳·贝尔·伯内尔", latinName: "Jocelyn Bell Burnell", years: "1943–", field: "天文", country: "英国", color: "violet", relation: "诞辰", tagline: "在噪声中听见脉冲星", story: "作为研究生，她在射电图纸上注意到规律脉冲，开启脉冲星发现。", contribution: "脉冲星发现", fact: "她将一笔大奖奖金捐出，用于支持少数群体进入物理学。" },
  { id: "noether", month: 7, day: 29, name: "埃米·诺特", latinName: "Emmy Noether", years: "1882–1935", field: "数学", country: "德国", color: "coral", relation: "诞辰", tagline: "每一种对称，背后都有守恒", story: "她证明了物理定律的连续对称性与守恒定律之间的深刻联系。", contribution: "诺特定理", fact: "时间平移对称对应能量守恒。" },
  { id: "schrodinger", month: 8, day: 12, name: "埃尔温·薛定谔", latinName: "Erwin Schrödinger", years: "1887–1961", field: "物理", country: "奥地利", color: "blue", relation: "诞辰", tagline: "用方程描述微观世界的波", story: "薛定谔方程成为量子力学的基础工具，描述量子态如何随时间演化。", contribution: "薛定谔方程", fact: "“薛定谔的猫”原本是他用来讨论量子解释的思想实验。" },
  { id: "broglie", month: 8, day: 15, name: "路易·德布罗意", latinName: "Louis de Broglie", years: "1892–1987", field: "物理", country: "法国", color: "blue", relation: "诞辰", tagline: "提出物质也有波的一面", story: "他大胆提出电子等粒子具有波动性，后来被实验验证。", contribution: "物质波", fact: "电子显微镜正是利用电子的波动性质提高分辨率。" },
  { id: "lavoisier", month: 8, day: 26, name: "安托万·拉瓦锡", latinName: "Antoine Lavoisier", years: "1743–1794", field: "化学", country: "法国", color: "green", relation: "诞辰", tagline: "把称量带进化学实验室", story: "他严谨测量反应前后的质量，推动质量守恒思想与现代化学命名。", contribution: "质量守恒与化学命名", fact: "他帮助确认氧在燃烧中的作用。" },
  { id: "lovelace", month: 12, day: 10, name: "艾达·洛芙莱斯", latinName: "Ada Lovelace", years: "1815–1852", field: "计算机", country: "英国", color: "coral", relation: "算法纪念", tagline: "想象机器不只会算数", story: "她在分析机笔记中写下了可执行步骤，并预见通用计算机可处理符号与音乐。", contribution: "早期程序思想", fact: "Ada 语言以她的名字命名。" },
  { id: "rutherford", month: 10, day: 30, name: "欧内斯特·卢瑟福", latinName: "Ernest Rutherford", years: "1871–1937", field: "物理", country: "新西兰 / 英国", color: "gold", relation: "诞辰", tagline: "看见原子内部几乎全是空旷", story: "金箔散射实验让原子核模型诞生，改变了人们对物质内部的想象。", contribution: "原子核模型", fact: "他曾说自己研究的不是物理，而是炼金术。" },
  { id: "cajal", month: 5, day: 1, name: "圣地亚哥·拉蒙-卡哈尔", latinName: "Santiago Ramón y Cajal", years: "1852–1934", field: "医学", country: "西班牙", color: "violet", relation: "诞辰", tagline: "画出神经元彼此独立的世界", story: "他借助染色技术描绘神经细胞，奠定了神经元学说。", contribution: "神经元学说", fact: "他的神经系统手绘图兼具科学与艺术价值。" },
  { id: "carson", month: 5, day: 27, name: "蕾切尔·卡森", latinName: "Rachel Carson", years: "1907–1964", field: "地球科学", country: "美国", color: "green", relation: "诞辰", tagline: "让生态系统进入公共讨论", story: "《寂静的春天》提醒公众关注农药对鸟类、生态与健康的连锁影响。", contribution: "环境科学传播", fact: "她早年曾在美国渔业机构从事海洋生物写作。" },
  { id: "mendel", month: 7, day: 20, name: "格雷戈尔·孟德尔", latinName: "Gregor Mendel", years: "1822–1884", field: "生命科学", country: "奥地利", color: "green", relation: "诞辰", tagline: "从豌豆中读出遗传规律", story: "长期的豌豆杂交实验让他提出遗传因子分离与组合的规律。", contribution: "遗传定律", fact: "孟德尔的工作在发表数十年后才被广泛重新发现。" },
  { id: "hopper", month: 12, day: 9, name: "格蕾丝·霍珀", latinName: "Grace Hopper", years: "1906–1992", field: "计算机", country: "美国", color: "coral", relation: "诞辰", tagline: "让程序更接近人类语言", story: "她推动编译器与高级编程语言发展，帮助计算机走出机器码的围墙。", contribution: "编译器与 COBOL", fact: "“debug”一词的著名轶事与她团队处理继电器飞蛾有关。" },
  { id: "goodall", month: 4, day: 3, name: "简·古道尔", latinName: "Jane Goodall", years: "1934–", field: "生命科学", country: "英国", color: "gold", relation: "诞辰", tagline: "重新认识黑猩猩，也重新认识人类", story: "她的长期野外观察显示黑猩猩会制作和使用工具。", contribution: "灵长类行为学", fact: "她在坦桑尼亚贡贝开展了数十年连续研究。" },
  { id: "vernadsky", month: 3, day: 12, name: "弗拉基米尔·维尔纳茨基", latinName: "Vladimir Vernadsky", years: "1863–1945", field: "地球科学", country: "乌克兰", color: "green", relation: "诞辰", tagline: "把生命看作塑造地球的力量", story: "他发展“生物圈”思想，强调生命与地球化学循环彼此交织。", contribution: "生物圈概念", fact: "他的思想影响了后来的地球系统科学。" },
  { id: "chandrasekhar", month: 10, day: 19, name: "苏布拉马尼扬·钱德拉塞卡", latinName: "S. Chandrasekhar", years: "1910–1995", field: "天文", country: "印度 / 美国", color: "blue", relation: "诞辰", tagline: "计算恒星坍缩前的极限", story: "他在年轻时推导出白矮星质量上限，为恒星演化和致密天体研究打下基础。", contribution: "钱德拉塞卡极限", fact: "他因恒星结构研究获得诺贝尔物理学奖。" },
  { id: "hubble", month: 11, day: 20, name: "埃德温·哈勃", latinName: "Edwin Hubble", years: "1889–1953", field: "天文", country: "美国", color: "gold", relation: "诞辰", tagline: "发现宇宙远比银河系辽阔", story: "他的观测表明许多“星云”是银河系外星系，并发现宇宙膨胀的证据。", contribution: "星系与宇宙膨胀观测", fact: "哈勃空间望远镜以他的名字命名。" },
];

const fields: Array<Field | "全部"> = ["全部", "物理", "化学", "生命科学", "数学", "计算机", "天文", "医学", "地球科学"];
const monthNames = ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"];
const weekdayNames = ["日", "一", "二", "三", "四", "五", "六"];

function formatDate(month: number, day: number) {
  return `${month} 月 ${day} 日`;
}

export default function Home() {
  const [activeField, setActiveField] = useState<Field | "全部">("全部");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState("noether");
  const [calendarMonth, setCalendarMonth] = useState(7);

  const selected = scientists.find((scientist) => scientist.id === selectedId) ?? scientists[0];
  const filtered = useMemo(() => scientists.filter((scientist) => {
    const inField = activeField === "全部" || scientist.field === activeField;
    const needle = query.trim().toLowerCase();
    const inSearch = !needle || [scientist.name, scientist.latinName, scientist.field, scientist.country, scientist.contribution].join(" ").toLowerCase().includes(needle);
    return inField && inSearch;
  }), [activeField, query]);

  const monthDays = new Date(2026, calendarMonth, 0).getDate();
  const firstWeekday = new Date(2026, calendarMonth - 1, 1).getDay();
  const monthEntries = scientists.filter((scientist) => scientist.month === calendarMonth);

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
          <div className="hero-actions"><a className="button-primary" href="#today">阅读今日人物 <span>↓</span></a><a className="text-link" href="#calendar">查看月历 <span>→</span></a></div>
        </div>
        <div className="orbit-art" aria-hidden="true">
          <div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="orbit orbit-three" />
          <div className="star star-a" /> <div className="star star-b" /> <div className="star star-c" />
          <div className="hero-disc"><span>365</span><small>种好奇</small></div>
          <p className="art-caption">每一个答案<br />都从一个问题开始</p>
        </div>
      </section>

      <section className="today-section" id="today" aria-labelledby="today-title">
        <header className="section-heading"><div><p className="eyebrow">TODAY&apos;S NOTE · {formatDate(selected.month, selected.day)}</p><h2 id="today-title">今日人物</h2></div><p className="section-aside">第 {String(selected.month).padStart(2, "0")}.{String(selected.day).padStart(2, "0")} 页 / 365</p></header>
        <article className={`feature-card tone-${selected.color}`}>
          <div className="portrait-panel"><span className="portrait-number">{String(selected.month).padStart(2, "0")}.{String(selected.day).padStart(2, "0")}</span><div className="portrait-monogram">{selected.name.slice(0, 1)}</div><span className="portrait-field">{selected.field}</span></div>
          <div className="feature-copy"><p className="feature-relation">{selected.relation} · {selected.years}</p><h3>{selected.name}</h3><p className="latin-name">{selected.latinName} · {selected.country}</p><p className="feature-tagline">“{selected.tagline}”</p><p className="feature-story">{selected.story}</p><div className="feature-meta"><div><span>核心贡献</span><strong>{selected.contribution}</strong></div><div><span>你知道吗</span><strong>{selected.fact}</strong></div></div><button className="detail-button" type="button" onClick={() => document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" })}>在档案库中继续探索 <span>→</span></button></div>
          <div className="feature-index" aria-hidden="true"><span>SCIENCE</span><span>NOTE</span><b>{selected.id.slice(0, 3).toUpperCase()}</b></div>
        </article>
      </section>

      <section className="calendar-section" id="calendar" aria-labelledby="calendar-title">
        <header className="section-heading"><div><p className="eyebrow">SCIENCE DATES · 2026</p><h2 id="calendar-title">月历</h2></div><div className="month-switcher"><button type="button" aria-label="上一个月" onClick={() => setCalendarMonth((month) => month === 1 ? 12 : month - 1)}>←</button><span>{monthNames[calendarMonth - 1]} 2026</span><button type="button" aria-label="下一个月" onClick={() => setCalendarMonth((month) => month === 12 ? 1 : month + 1)}>→</button></div></header>
        <div className="calendar-layout"><div className="calendar-grid" role="grid" aria-label={`${calendarMonth} 月日历`}><div className="weekdays">{weekdayNames.map((day) => <span key={day}>{day}</span>)}</div><div className="dates">{Array.from({ length: firstWeekday }, (_, index) => <span className="blank-day" key={`blank-${index}`} />)}{Array.from({ length: monthDays }, (_, index) => { const day = index + 1; const entry = monthEntries.find((scientist) => scientist.day === day); return <button className={`date-cell ${entry ? `has-entry ${entry.id === selected.id ? "selected" : ""}` : ""}`} type="button" key={day} onClick={() => entry && selectScientist(entry)} disabled={!entry} aria-label={entry ? `${day} 日：${entry.name}` : `${day} 日没有收录人物`}><span>{day}</span>{entry && <i className={`dot ${entry.color}`} />}</button>; })}</div></div>
          <aside className="calendar-notes"><p className="eyebrow">THIS MONTH</p><h3>{monthEntries.length ? `${monthEntries.length} 个科学瞬间` : "正在整理中"}</h3>{monthEntries.length ? monthEntries.map((entry) => <button className="month-entry" type="button" key={entry.id} onClick={() => selectScientist(entry)}><span>{String(entry.day).padStart(2, "0")}</span><div><strong>{entry.name}</strong><small>{entry.relation} · {entry.field}</small></div><b>↗</b></button>) : <p>这一页将留给新的好奇心。</p>}<p className="calendar-tip">带有彩色圆点的日期，收录了一则科学人物或科学史纪念。</p></aside></div>
      </section>

      <section className="explore-section" id="explore" aria-labelledby="explore-title">
        <header className="section-heading explore-heading"><div><p className="eyebrow">THE ARCHIVE · 30 STARTING POINTS</p><h2 id="explore-title">从好奇出发</h2></div><label className="search-box"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索人物、领域或贡献" aria-label="搜索科学家档案" /></label></header>
        <div className="field-filters" aria-label="按科学领域筛选">{fields.map((field) => <button key={field} type="button" className={field === activeField ? "active" : ""} onClick={() => setActiveField(field)}>{field}</button>)}</div>
        <div className="archive-grid">{filtered.map((scientist, index) => <button className={`archive-card tone-${scientist.color}`} type="button" key={scientist.id} onClick={() => selectScientist(scientist)}><span className="archive-date">{String(scientist.month).padStart(2, "0")}.{String(scientist.day).padStart(2, "0")}</span><span className="archive-monogram">{scientist.name.slice(0, 1)}</span><span className="archive-field">{scientist.field}</span><h3>{scientist.name}</h3><p>{scientist.tagline}</p><span className="archive-open">阅读档案 <b>↗</b></span><i className="archive-index">{String(index + 1).padStart(2, "0")}</i></button>)}</div>
        {!filtered.length && <p className="empty-state">没有找到匹配的人物。换个关键词试试。</p>}
      </section>

      <section className="manifesto" id="about"><p className="eyebrow">WHY A SCIENCE CALENDAR</p><p>科学并非一串遥远的姓名与年份，<br />而是一代代人对世界的<strong>耐心注视</strong>。</p><span>收藏今天的好奇，明天继续提问。</span></section>

      <footer><a className="brand" href="#top"><span className="brand-mark">∴</span> 科学家日历</a><p>首批 30 则人物档案 · 持续更新中</p><a href="#top">回到顶部 ↑</a></footer>
    </main>
  );
}
