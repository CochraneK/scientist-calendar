import type { Metadata } from "next";
import "./globals.css";

// 固定站点 URL（Pages base path = /scientist-calendar/），不依赖请求的 Host Header，
// 避免反向代理或本地预览下 canonical / openGraph 链接错乱。
const SITE_URL = "https://cochranek.github.io/scientist-calendar/";
const OG_IMAGE = "https://cochranek.github.io/scientist-calendar/og.jpg";

export async function generateMetadata(): Promise<Metadata> {
  const title = "科学家日历｜每天认识一位科学家";
  const description = "一份写给好奇心的科学日历：每天认识一位科学家、一项发现与一个改变世界的念头。";

  return {
    title,
    description,
    metadataBase: new URL(SITE_URL),
    alternates: { canonical: SITE_URL },
    openGraph: {
      title,
      description,
      url: SITE_URL,
      siteName: "科学家日历",
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
