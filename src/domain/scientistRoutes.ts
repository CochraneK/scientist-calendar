export const SITE_ORIGIN = "https://cochranek.github.io";
export const SITE_BASE_PATH = "/scientist-calendar";
export const SITE_URL = `${SITE_ORIGIN}${SITE_BASE_PATH}/`;

function normalizeBasePath(basePath: string): string {
  if (!basePath || basePath === "/") return "";
  return `/${basePath.replace(/^\/+|\/+$/g, "")}`;
}

export function scientistPath(id: string, basePath: string = SITE_BASE_PATH): string {
  const base = normalizeBasePath(basePath);
  return `${base}/scientists/${encodeURIComponent(id)}/`;
}

export function scientistAbsoluteUrl(id: string): string {
  return `${SITE_ORIGIN}${scientistPath(id)}`;
}

export function scientistBrowserPath(id: string, currentPathname: string): string {
  const basePath = currentPathname === SITE_BASE_PATH || currentPathname.startsWith(`${SITE_BASE_PATH}/`)
    ? SITE_BASE_PATH
    : "";
  return scientistPath(id, basePath);
}

export function scientistIdFromPath(pathname: string): string | null {
  const marker = "/scientists/";
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
