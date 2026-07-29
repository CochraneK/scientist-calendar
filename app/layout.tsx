import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "localhost:3000";
  const protocol = requestHeaders.get("x-forwarded-proto") ?? "https";
  const title = "科学家日历｜每天认识一位科学家";
  const description = "一份写给好奇心的科学日历：每天认识一位科学家、一项发现与一个改变世界的念头。";

  return {
    title,
    description,
    metadataBase: new URL(`${protocol}://${host}`),
    openGraph: { title, description, images: ["/og.png"], type: "website", locale: "zh_CN" },
    twitter: { card: "summary_large_image", title, description, images: ["/og.png"] },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
