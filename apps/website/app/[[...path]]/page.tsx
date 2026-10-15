import type { Metadata } from "next";
import { notFound, permanentRedirect, redirect } from "next/navigation";

import { countries, entry, type Entry, posts, redirects, type Settings, settings } from "@/api";
import { Blocks, PostGrid } from "@/blocks";
import { EntryView } from "@/EntryView";
import { DEFAULT_MEDIA, DEFAULT_PAGES } from "@/defaults";

// Every content address (D83): pages and posts published in Admin > Website, the blog, and
// built-in pages until the same address is published. /pricing and /legal have their own
// routes because they always read Admin > Plans & Pricing and Admin > Legal documents.

export const revalidate = 300;

type Params = { params: Promise<{ path?: string[] }>; searchParams: Promise<Record<string, string | undefined>> };

type Route =
  | { kind: "page"; locale: string; slug: string }
  | { kind: "post"; locale: string; slug: string }
  | { kind: "blog"; locale: string };

function route(path: string[], s: Settings): Route {
  let parts = path.map((p) => decodeURIComponent(p));
  let locale = s.default_locale;
  if (parts[0] && parts[0] !== s.default_locale && s.locales.includes(parts[0])) {
    locale = parts[0];
    parts = parts.slice(1);
  }
  if (parts[0] === "blog" && parts.length === 1) return { kind: "blog", locale };
  if (parts[0] === "blog" && parts.length === 2) return { kind: "post", locale, slug: parts[1] ?? "" };
  return { kind: "page", locale, slug: parts.join("/") };
}

async function load(r: Route): Promise<Entry | null> {
  if (r.kind === "blog") return null;
  return entry(r.kind, r.locale, r.slug);
}

async function followRedirect(path: string[]) {
  const here = `/${path.join("/")}`;
  const r = (await redirects()).find((x) => x.from_path.replace(/\/$/, "") === here.replace(/\/$/, ""));
  if (r) (r.permanent ? permanentRedirect : redirect)(r.to_path);
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { path = [] } = await params;
  const s = await settings();
  const r = route(path, s);
  if (r.kind === "blog") return { title: "Blog", alternates: { canonical: r.locale === s.default_locale ? "/blog" : `/${r.locale}/blog` } };
  const e = await load(r);
  if (!e) {
    const d = r.kind === "page" && r.locale === s.default_locale ? DEFAULT_PAGES[r.slug] : undefined;
    return d ? { title: r.slug ? d.title : { absolute: `${s.site_name}: ${d.title}` }, description: d.description } : {};
  }
  const content = e.content as { title: string; excerpt?: string; seo?: { title?: string; description?: string; image_id?: string; noindex?: boolean }; cover_id?: string };
  const imageId = content.seo?.image_id ?? content.cover_id;
  const image = imageId ? (e.media as Record<string, { url: string }>)[imageId]?.url : undefined;
  const languages = Object.fromEntries(e.alternates.map((a) => [a.locale, a.path]));
  return {
    title: content.seo?.title ?? content.title,
    description: content.seo?.description ?? content.excerpt,
    alternates: { canonical: e.path, languages },
    openGraph: {
      title: content.seo?.title ?? content.title,
      description: content.seo?.description ?? content.excerpt,
      type: e.kind === "post" ? "article" : "website",
      images: image ? [image] : undefined,
    },
    robots: content.seo?.noindex ? { index: false, follow: true } : undefined,
  };
}

export default async function Page({ params, searchParams }: Params) {
  const { path = [] } = await params;
  const s = await settings();
  const r = route(path, s);
  const list = await countries();

  if (r.kind === "blog") {
    const { before, tag } = await searchParams;
    const page = await posts(r.locale, before, tag);
    return (
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <h1 className="font-display text-4xl font-semibold tracking-tight text-ink">{tag ? `Posts tagged “${tag}”` : "Blog"}</h1>
        <div className="mt-10">
          <PostGrid posts={page.data} />
        </div>
        {page.next_cursor ? (
          <p className="mt-10 text-center">
            <a href={`?before=${encodeURIComponent(page.next_cursor)}${tag ? `&tag=${encodeURIComponent(tag)}` : ""}`} className="text-blue hover:underline">
              Older posts
            </a>
          </p>
        ) : null}
      </section>
    );
  }

  const e = await load(r);
  if (!e) {
    const d = r.kind === "page" && r.locale === s.default_locale ? DEFAULT_PAGES[r.slug] : undefined;
    if (d) return <Blocks blocks={d.blocks} ctx={{ media: DEFAULT_MEDIA, locale: r.locale, posts: [], countries: list }} />;
    await followRedirect(path);
    notFound();
  }
  return <EntryView e={e} countries={list} />;
}
