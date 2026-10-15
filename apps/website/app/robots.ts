import type { MetadataRoute } from "next";

import { settings } from "@/api";

export const revalidate = 300;

export default async function Robots(): Promise<MetadataRoute.Robots> {
  const s = await settings();
  const base = s.base_url.replace(/\/$/, "");
  return { rules: [{ userAgent: "*", allow: "/", disallow: ["/preview", "/api/"] }], sitemap: `${base}/sitemap.xml` };
}
