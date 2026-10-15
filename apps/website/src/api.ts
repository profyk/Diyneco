/**
 * Server-side reads from the Diyneco API (D83). Everything is public and cached for five
 * minutes; publishing in the Admin panel asks the site to refresh at once (/api/revalidate).
 * A failed read returns null so a page can fall back instead of failing the whole site.
 */
import type { components } from "@diyneco/api-client";

export type Settings = components["schemas"]["PublicSettings"];
export type Entry = components["schemas"]["PublicEntry"];
export type PostCard = components["schemas"]["PostCard"];
export type Plans = components["schemas"]["PublicPlanList"];
export type Plan = components["schemas"]["PublicPlan"];
export type LegalDoc = components["schemas"]["LegalDocumentOut"];
export type Redirect = components["schemas"]["RedirectOut"];
export type SitemapEntry = components["schemas"]["SitemapEntry"];

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
export const MERCHANT_URL = (process.env.NEXT_PUBLIC_MERCHANT_URL ?? "http://localhost:3001").replace(/\/$/, "");
export const REVALIDATE_S = 300;

async function get<T>(path: string, query: Record<string, string | undefined> = {}, fresh = false): Promise<T | null> {
  const qs = new URLSearchParams(Object.entries(query).filter(([, v]) => v !== undefined) as [string, string][]);
  const url = `${API_URL}/api/v1${path}${qs.size ? `?${qs}` : ""}`;
  try {
    const res = await fetch(url, fresh ? { cache: "no-store" } : { next: { revalidate: REVALIDATE_S } });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null; // API unreachable (e.g. while building): pages show their defaults
  }
}

export const DEFAULT_SETTINGS: Settings = {
  site_name: "Diyneco",
  base_url: "https://www.diyneco.com",
  default_locale: "en",
  locales: ["en"],
  navigation: [],
  footer: {},
  contact: {},
  social: [],
  seo: { title_template: "%s | Diyneco" },
  verification: {},
  analytics: { provider: "builtin" },
  media: {},
};

export async function settings(): Promise<Settings> {
  return (await get<Settings>("/site/settings")) ?? DEFAULT_SETTINGS;
}

export function entry(kind: "page" | "post", locale: string, slug: string): Promise<Entry | null> {
  return get<Entry>("/site/entry", { kind, locale, slug });
}

export function preview(token: string): Promise<Entry | null> {
  return get<Entry>("/site/preview", { token }, true);
}

export async function posts(locale: string, before?: string, tag?: string, limit = 12) {
  return (
    (await get<components["schemas"]["PostCardList"]>("/site/posts", { locale, before, tag, limit: String(limit) })) ?? {
      data: [],
      next_cursor: null,
    }
  );
}

export async function redirects(): Promise<Redirect[]> {
  return (await get<components["schemas"]["RedirectList"]>("/site/redirects"))?.data ?? [];
}

export async function sitemap(): Promise<SitemapEntry[]> {
  return (await get<components["schemas"]["Sitemap"]>("/site/sitemap"))?.data ?? [];
}

/** Published plans and prices from Admin > Plans & Pricing: the site never keeps its own. */
export function plans(): Promise<Plans | null> {
  return get<Plans>("/plans");
}

/** Current legal documents from Admin > Legal documents (country-specific where they exist). */
export async function legalDocuments(country?: string): Promise<LegalDoc[]> {
  return (await get<components["schemas"]["LegalDocumentList"]>("/legal/documents", { country, audience: "all" }))?.data ?? [];
}

/** Countries open for signups (Admin > Countries), for the contact form. */
export async function countries(): Promise<{ code: string; name: string }[]> {
  const list = await get<components["schemas"]["CountryList"]>("/countries");
  return (list?.data ?? []).map((c) => ({ code: c.code, name: c.name }));
}

export function mediaUrl(path: string): string {
  return path.startsWith("http") ? path : `${API_URL}${path}`;
}
