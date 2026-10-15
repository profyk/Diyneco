import type { MetadataRoute } from "next";

import { settings, sitemap } from "@/api";

export const revalidate = 300;

export default async function Sitemap(): Promise<MetadataRoute.Sitemap> {
  const s = await settings();
  const base = s.base_url.replace(/\/$/, "");
  const published = await sitemap();
  const fixed = ["/", "/pricing", "/blog", "/contact", "/demo", "/legal"].filter((p) => !published.some((e) => e.path === p));
  return [
    ...fixed.map((p) => ({ url: `${base}${p}` })),
    ...published.map((e) => ({
      url: `${base}${e.path}`,
      lastModified: e.updated_at,
      alternates: { languages: Object.fromEntries(e.alternates.map((a) => [a.locale, `${base}${a.path}`])) },
    })),
  ];
}
