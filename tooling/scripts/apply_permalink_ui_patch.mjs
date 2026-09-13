import { readFileSync, writeFileSync } from "node:fs";

const pagePath = "app/page.tsx";
let source = readFileSync(pagePath, "utf8");
const lines = (...items) => items.join("\n");

function replaceOnce(search, replacement, label) {
  const matches = source.split(search).length - 1;
  if (matches !== 1) throw new Error(`${label}: expected exactly one match, found ${matches}`);
  source = source.replace(search, replacement);
}

replaceOnce(
  'import { useCurrentDate } from "../src/hooks/useCurrentDate";',
  lines(
    'import { useCurrentDate } from "../src/hooks/useCurrentDate";',
    'import { SITE_BASE_PATH, SITE_URL, scientistAbsoluteUrl, scientistBrowserPath, scientistIdFromPath } from "../src/domain/scientistRoutes";',
  ),
  "route imports",
);

replaceOnce(
  'const einsteinIllustration = "art/einstein-archive.webp";',
  lines(
    'const runtimeBasePath = typeof window !== "undefined" && (window.location.pathname === SITE_BASE_PATH || window.location.pathname.startsWith(`${SITE_BASE_PATH}/`))',
    '  ? SITE_BASE_PATH',
    '  : "";',
    'function assetPath(path: string): string {',
    '  return `${runtimeBasePath}/${path.replace(/^\\/+/, "")}`;',
    '}',
    'const einsteinIllustration = assetPath("art/einstein-archive.webp");',
  ),
  "asset base path",
);

replaceOnce(
  'if (avatars[scientist.id]?.photo) return `avatars/${scientist.id}.jpg`;',
  'if (avatars[scientist.id]?.photo) return assetPath(`avatars/${scientist.id}.jpg`);',
  "avatar asset path",
);

replaceOnce(
  lines(
    'function formatDate(month: number, day: number) {',
    '  return `${month} 月 ${day} 日`;',
    '}',
  ),
  lines(
    'function formatDate(month: number, day: number) {',
    '  return `${month} 月 ${day} 日`;',
    '}',
    '',
    'const HOME_TITLE = "科学家日历｜每天认识一位科学家";',
    'const HOME_DESCRIPTION = "一份写给好奇心的科学日历：每天认识一位科学家、一项发现与一个改变世界的念头。";',
    '',
    'function initialScientistRouteId(): string | null {',
    '  if (typeof window === "undefined") return null;',
    '  const routeId = scientistIdFromPath(window.location.pathname);',
    '  return routeId && scientists.some((scientist) => scientist.id === routeId) ? routeId : null;',
    '}',
    '',
    'function scientistDescription(scientist: ScientistSummary): string {',
    '  const description = `${scientist.name}（${scientist.latinName}）｜${scientist.country} · ${scientist.field}｜${scientist.tagline}。核心贡献：${scientist.contribution}`;',
    '  return description.length > 170 ? `${description.slice(0, 167)}…` : description;',
    '}',
    '',
    'function updateMeta(selector: string, content: string) {',
    '  document.querySelector<HTMLMetaElement>(selector)?.setAttribute("content", content);',
    '}',
    '',
    'function applyPageMetadata(scientist: ScientistSummary | null) {',
    '  const title = scientist ? `${scientist.name}｜科学家日历` : HOME_TITLE;',
    '  const description = scientist ? scientistDescription(scientist) : HOME_DESCRIPTION;',
    '  const url = scientist ? scientistAbsoluteUrl(scientist.id) : SITE_URL;',
    '  document.title = title;',
    "  updateMeta('meta[name=\"description\"]', description);",
    "  updateMeta('meta[property=\"og:title\"]', title);",
    "  updateMeta('meta[property=\"og:description\"]', description);",
    "  updateMeta('meta[property=\"og:url\"]', url);",
    "  updateMeta('meta[property=\"og:type\"]', scientist ? \"profile\" : \"website\");",
    "  updateMeta('meta[name=\"twitter:title\"]', title);",
    "  updateMeta('meta[name=\"twitter:description\"]', description);",
    "  document.querySelector<HTMLLinkElement>('link[rel=\"canonical\"]')?.setAttribute(\"href\", url);",
    '}',
  ),
  "metadata helpers",
);

replaceOnce(
  'const [selectedId, setSelectedId] = useState(todayScientist?.id ?? "einstein");',
  lines(
    'const [selectedId, setSelectedId] = useState(() => initialScientistRouteId() ?? todayScientist?.id ?? "einstein");',
    '  const [profileRouteId, setProfileRouteId] = useState<string | null>(() => initialScientistRouteId());',
  ),
  "initial route state",
);

replaceOnce(
  'const [detailRetryToken, setDetailRetryToken] = useState(0);',
  lines(
    'const [detailRetryToken, setDetailRetryToken] = useState(0);',
    '  const [shareNotice, setShareNotice] = useState("");',
  ),
  "share state",
);

replaceOnce(
  'const detailLoadFailed = detailLoadErrors.has(selected.month);',
  lines(
    'const detailLoadFailed = detailLoadErrors.has(selected.month);',
    '',
    '  useEffect(() => {',
    '    applyPageMetadata(profileRouteId === selected.id ? selected : null);',
    '  }, [profileRouteId, selected]);',
    '',
    '  useEffect(() => {',
    '    if (typeof window === "undefined") return;',
    '    const routeId = scientistIdFromPath(window.location.pathname);',
    '    if (routeId) {',
    '      const frame = window.requestAnimationFrame(() => {',
    '        document.getElementById("today")?.scrollIntoView({ block: "start" });',
    '      });',
    '      return () => window.cancelAnimationFrame(frame);',
    '    }',
    '  }, []);',
    '',
    '  useEffect(() => {',
    '    if (typeof window === "undefined") return;',
    '    const handlePopState = () => {',
    '      const routeId = scientistIdFromPath(window.location.pathname);',
    '      const target = routeId ? scientists.find((scientist) => scientist.id === routeId) : todayScientist;',
    '      if (!target) return;',
    '      setProfileRouteId(routeId && target.id === routeId ? routeId : null);',
    '      setSelectedId(target.id);',
    '      setCalendarMonth(target.month);',
    '      setShareNotice("");',
    '    };',
    '    window.addEventListener("popstate", handlePopState);',
    '    return () => window.removeEventListener("popstate", handlePopState);',
    '  }, [todayScientist]);',
  ),
  "route effects",
);

replaceOnce(
  lines(
    '  function selectScientist(scientist: ScientistSummary) {',
    '    setSelectedId(scientist.id);',
    '    setCalendarMonth(scientist.month);',
    '    document.getElementById("today")?.scrollIntoView({ behavior: "smooth", block: "start" });',
    '  }',
  ),
  lines(
    '  function selectScientist(scientist: ScientistSummary) {',
    '    if (typeof window !== "undefined") {',
    '      const path = scientistBrowserPath(scientist.id, window.location.pathname);',
    '      if (window.location.pathname !== path) window.history.pushState({ scientistId: scientist.id }, "", path);',
    '    }',
    '    setProfileRouteId(scientist.id);',
    '    setSelectedId(scientist.id);',
    '    setCalendarMonth(scientist.month);',
    '    setShareNotice("");',
    '    document.getElementById("today")?.scrollIntoView({ behavior: "smooth", block: "start" });',
    '  }',
  ),
  "selectScientist routing",
);

replaceOnce(
  lines(
    '  function cycleDayScientist(day: number) {',
    '    const dayEntries = monthEntriesByDay.get(day) ?? [];',
    '    if (!dayEntries.length) return;',
    '    const currentIndex = dayEntries.findIndex((e) => e.id === selected.id);',
    '    const next = dayEntries[(currentIndex + 1) % dayEntries.length];',
    '    selectScientist(next);',
    '  }',
  ),
  lines(
    '  function cycleDayScientist(day: number) {',
    '    const dayEntries = monthEntriesByDay.get(day) ?? [];',
    '    if (!dayEntries.length) return;',
    '    const currentIndex = dayEntries.findIndex((e) => e.id === selected.id);',
    '    const next = dayEntries[(currentIndex + 1) % dayEntries.length];',
    '    selectScientist(next);',
    '  }',
    '',
    '  async function shareSelectedScientist() {',
    '    const url = scientistAbsoluteUrl(selected.id);',
    '    const data = {',
    '      title: `${selected.name}｜科学家日历`,',
    '      text: `认识 ${selected.name}：${selected.tagline}`,',
    '      url,',
    '    };',
    '    try {',
    '      if (navigator.share) {',
    '        await navigator.share(data);',
    '        setShareNotice("已打开系统分享");',
    '        return;',
    '      }',
    '      if (navigator.clipboard?.writeText) {',
    '        await navigator.clipboard.writeText(url);',
    '        setShareNotice("人物链接已复制");',
    '        return;',
    '      }',
    '      window.prompt("复制人物链接", url);',
    '      setShareNotice("可复制上方人物链接");',
    '    } catch (error) {',
    '      if (error instanceof DOMException && error.name === "AbortError") return;',
    '      setShareNotice("分享失败，请复制地址栏链接");',
    '    }',
    '  }',
  ),
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
