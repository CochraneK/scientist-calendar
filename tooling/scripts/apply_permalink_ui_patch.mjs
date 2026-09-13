import { readFileSync, writeFileSync } from "node:fs";

const pagePath = "app/page.tsx";
let source = readFileSync(pagePath, "utf8");

function replaceOnce(search, replacement, label) {
  const matches = typeof search === "string"
    ? source.split(search).length - 1
    : [...source.matchAll(new RegExp(search.source, search.flags.includes("g") ? search.flags : `${search.flags}g`))].length;
  if (matches !== 1) throw new Error(`${label}: expected exactly one match, found ${matches}`);
  source = source.replace(search, replacement);
}

replaceOnce(
  'import { useCurrentDate } from "../src/hooks/useCurrentDate";',
  'import { useCurrentDate } from "../src/hooks/useCurrentDate";\nimport { SITE_BASE_PATH, SITE_URL, scientistAbsoluteUrl, scientistBrowserPath, scientistIdFromPath } from "../src/domain/scientistRoutes";',
  "route imports",
);

replaceOnce(
  'const einsteinIllustration = "art/einstein-archive.webp";',
  `const runtimeBasePath = typeof window !== "undefined" && (window.location.pathname === SITE_BASE_PATH || window.location.pathname.startsWith(\`${SITE_BASE_PATH}/\`))\n  ? SITE_BASE_PATH\n  : "";\nfunction assetPath(path: string): string {\n  return \`${runtimeBasePath}/\${path.replace(/^\\/+/, "")}\`;\n}\nconst einsteinIllustration = assetPath("art/einstein-archive.webp");`,
  "asset base path",
);

replaceOnce(
  'if (avatars[scientist.id]?.photo) return `avatars/${scientist.id}.jpg`;',
  'if (avatars[scientist.id]?.photo) return assetPath(`avatars/${scientist.id}.jpg`);',
  "avatar asset path",
);

replaceOnce(
  'function formatDate(month: number, day: number) {\n  return `${month} 月 ${day} 日`;\n}',
  `function formatDate(month: number, day: number) {\n  return \`${month} 月 \${day} 日\`;\n}\n\nconst HOME_TITLE = "科学家日历｜每天认识一位科学家";\nconst HOME_DESCRIPTION = "一份写给好奇心的科学日历：每天认识一位科学家、一项发现与一个改变世界的念头。";\n\nfunction initialScientistRouteId(): string | null {\n  if (typeof window === "undefined") return null;\n  const routeId = scientistIdFromPath(window.location.pathname);\n  return routeId && scientists.some((scientist) => scientist.id === routeId) ? routeId : null;\n}\n\nfunction scientistDescription(scientist: ScientistSummary): string {\n  const description = \`${scientist.name}（\${scientist.latinName}）｜\${scientist.country} · \${scientist.field}｜\${scientist.tagline}。核心贡献：\${scientist.contribution}\`;\n  return description.length > 170 ? \`\${description.slice(0, 167)}…\` : description;\n}\n\nfunction updateMeta(selector: string, content: string) {\n  document.querySelector<HTMLMetaElement>(selector)?.setAttribute("content", content);\n}\n\nfunction applyPageMetadata(scientist: ScientistSummary | null) {\n  const title = scientist ? \`\${scientist.name}｜科学家日历\` : HOME_TITLE;\n  const description = scientist ? scientistDescription(scientist) : HOME_DESCRIPTION;\n  const url = scientist ? scientistAbsoluteUrl(scientist.id) : SITE_URL;\n  document.title = title;\n  updateMeta('meta[name="description"]', description);\n  updateMeta('meta[property="og:title"]', title);\n  updateMeta('meta[property="og:description"]', description);\n  updateMeta('meta[property="og:url"]', url);\n  updateMeta('meta[property="og:type"]', scientist ? "profile" : "website");\n  updateMeta('meta[name="twitter:title"]', title);\n  updateMeta('meta[name="twitter:description"]', description);\n  document.querySelector<HTMLLinkElement>('link[rel="canonical"]')?.setAttribute("href", url);\n}`,
  "metadata helpers",
);

replaceOnce(
  'const [selectedId, setSelectedId] = useState(todayScientist?.id ?? "einstein");',
  'const [selectedId, setSelectedId] = useState(() => initialScientistRouteId() ?? todayScientist?.id ?? "einstein");\n  const [profileRouteId, setProfileRouteId] = useState<string | null>(() => initialScientistRouteId());',
  "initial route state",
);

replaceOnce(
  'const [detailRetryToken, setDetailRetryToken] = useState(0);',
  'const [detailRetryToken, setDetailRetryToken] = useState(0);\n  const [shareNotice, setShareNotice] = useState("");',
  "share state",
);

replaceOnce(
  'const detailLoadFailed = detailLoadErrors.has(selected.month);',
  `const detailLoadFailed = detailLoadErrors.has(selected.month);\n\n  useEffect(() => {\n    applyPageMetadata(profileRouteId === selected.id ? selected : null);\n  }, [profileRouteId, selected]);\n\n  useEffect(() => {\n    if (typeof window === "undefined") return;\n    const routeId = scientistIdFromPath(window.location.pathname);\n    if (routeId) {\n      const frame = window.requestAnimationFrame(() => {\n        document.getElementById("today")?.scrollIntoView({ block: "start" });\n      });\n      return () => window.cancelAnimationFrame(frame);\n    }\n  }, []);\n\n  useEffect(() => {\n    if (typeof window === "undefined") return;\n    const handlePopState = () => {\n      const routeId = scientistIdFromPath(window.location.pathname);\n      const target = routeId ? scientists.find((scientist) => scientist.id === routeId) : todayScientist;\n      if (!target) return;\n      setProfileRouteId(routeId && target.id === routeId ? routeId : null);\n      setSelectedId(target.id);\n      setCalendarMonth(target.month);\n      setShareNotice("");\n    };\n    window.addEventListener("popstate", handlePopState);\n    return () => window.removeEventListener("popstate", handlePopState);\n  }, [todayScientist]);`,
  "route effects",
);

replaceOnce(
  `  function selectScientist(scientist: ScientistSummary) {\n    setSelectedId(scientist.id);\n    setCalendarMonth(scientist.month);\n    document.getElementById("today")?.scrollIntoView({ behavior: "smooth", block: "start" });\n  }`,
  `  function selectScientist(scientist: ScientistSummary) {\n    if (typeof window !== "undefined") {\n      const path = scientistBrowserPath(scientist.id, window.location.pathname);\n      if (window.location.pathname !== path) window.history.pushState({ scientistId: scientist.id }, "", path);\n    }\n    setProfileRouteId(scientist.id);\n    setSelectedId(scientist.id);\n    setCalendarMonth(scientist.month);\n    setShareNotice("");\n    document.getElementById("today")?.scrollIntoView({ behavior: "smooth", block: "start" });\n  }`,
  "selectScientist routing",
);

replaceOnce(
  `  function cycleDayScientist(day: number) {\n    const dayEntries = monthEntriesByDay.get(day) ?? [];\n    if (!dayEntries.length) return;\n    const currentIndex = dayEntries.findIndex((e) => e.id === selected.id);\n    const next = dayEntries[(currentIndex + 1) % dayEntries.length];\n    selectScientist(next);\n  }`,
  `  function cycleDayScientist(day: number) {\n    const dayEntries = monthEntriesByDay.get(day) ?? [];\n    if (!dayEntries.length) return;\n    const currentIndex = dayEntries.findIndex((e) => e.id === selected.id);\n    const next = dayEntries[(currentIndex + 1) % dayEntries.length];\n    selectScientist(next);\n  }\n\n  async function shareSelectedScientist() {\n    const url = scientistAbsoluteUrl(selected.id);\n    const data = {\n      title: \`\${selected.name}｜科学家日历\`,\n      text: \`认识 \${selected.name}：\${selected.tagline}\`,\n      url,\n    };\n    try {\n      if (navigator.share) {\n        await navigator.share(data);\n        setShareNotice("已打开系统分享");\n        return;\n      }\n      if (navigator.clipboard?.writeText) {\n        await navigator.clipboard.writeText(url);\n        setShareNotice("人物链接已复制");\n        return;\n      }\n      window.prompt("复制人物链接", url);\n      setShareNotice("可复制上方人物链接");\n    } catch (error) {\n      if (error instanceof DOMException && error.name === "AbortError") return;\n      setShareNotice("分享失败，请复制地址栏链接");\n    }\n  }`,
  "share handler",
);

replaceOnce(
  'href={`print/科学家日历_精选${scientists.length}位_A4打印版.pdf`}',
  'href={assetPath(`print/科学家日历_精选${scientists.length}位_A4打印版.pdf`)}',
  "hero daily PDF path",
);
replaceOnce(
  'href="print/科学家日历_月度生日版_A4.pdf"',
  'href={assetPath("print/科学家日历_月度生日版_A4.pdf")}',
  "monthly PDF path",
);
replaceOnce(
  'href={`print/科学家日历_精选${scientists.length}位_A4打印版.pdf`}',
  'href={assetPath(`print/科学家日历_精选${scientists.length}位_A4打印版.pdf`)}',
  "footer daily PDF path",
);

replaceOnce(
  '<button className="detail-button" type="button" onClick={() => document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" })}>在档案库中继续探索 <span>→</span></button>',
  '<button className="detail-button" type="button" onClick={() => { void shareSelectedScientist(); }}>分享人物 <span>↗</span></button>{shareNotice && <span className="share-notice" role="status" aria-live="polite">{shareNotice}</span>}<button className="detail-button" type="button" onClick={() => document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" })}>在档案库中继续探索 <span>→</span></button>',
  "share button",
);

writeFileSync(pagePath, source, "utf8");
console.log("✓ permalink/share UI patch applied");
