// 站点路由：所有 URL 拼装从 siteConfig 取，不再硬编码「scientist-calendar」。
import { SITE_CONFIG } from "./siteConfig.ts";

export const SITE_ORIGIN = SITE_CONFIG.origin;
export const SITE_BASE_PATH = SITE_CONFIG.basePath;
export const SITE_URL = `${SITE_ORIGIN}${SITE_BASE_PATH}/`;

function normalizeBasePath(basePath: string): string {
  if (!basePath || basePath === "/") return "";
  return `/${basePath.replace(/^\/+|\/+$/g, "")}`;
}

export function entryPath(id: string, basePath: string = SITE_BASE_PATH): string {
  const base = normalizeBasePath(basePath);
  return `${base}/${SITE_CONFIG.entryRouteSegment}/${encodeURIComponent(id)}/`;
}

// 兼容旧命名（app/page.tsx 等已按 entry* 重命名，这里保留别名便于渐进迁移）
export const scientistPath = entryPath;
export const scientistAbsoluteUrl = (id: string): string => `${SITE_ORIGIN}${entryPath(id)}`;

export function scientistBrowserPath(id: string, currentPathname: string): string {
  const basePath = currentPathname === SITE_BASE_PATH || currentPathname.startsWith(`${SITE_BASE_PATH}/`)
    ? SITE_BASE_PATH
    : "";
  return entryPath(id, basePath);
}

export function scientistIdFromPath(pathname: string): string | null {
  const marker = `/${SITE_CONFIG.entryRouteSegment}/`;
  const markerIndex = pathname.indexOf(marker);
  if (markerIndex < 0) return null;

  const encodedId = pathname.slice(markerIndex + marker.length).split("/")[0];
  if (!encodedId) return null;

  try {
    return decodeURIComponent(encodedId);
  } catch {
    return null;
  }
}
