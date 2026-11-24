import type { Metadata } from "next";
import "./globals.css";
import { SITE_CONFIG, homeTitle } from "../src/domain/siteConfig";

// 固定站点 URL（Pages base path 从 theme.json 注入），不依赖请求的 Host Header，
// 避免反向代理或本地预览下 canonical / openGraph 链接错乱。
const SITE_URL = `${SITE_CONFIG.origin}${SITE_CONFIG.basePath}/`;
const OG_IMAGE = `${SITE_CONFIG.origin}${SITE_CONFIG.basePath}/og.jpg`;

export async function generateMetadata(): Promise<Metadata> {
  const title = homeTitle();
  const description = SITE_CONFIG.description;

  return {
    title,
    description,
    metadataBase: new URL(SITE_URL),
    alternates: { canonical: SITE_URL },
    openGraph: {
      title,
      description,
      url: SITE_URL,
      siteName: SITE_CONFIG.name,
      images: [OG_IMAGE],
      type: "website",
      locale: "zh_CN",
    },
    twitter: { card: "summary_large_image", title, description, images: [OG_IMAGE] },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
