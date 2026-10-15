import type { Entry } from "./api";
import { Blocks } from "./blocks";
import { Markdown } from "./markdown";

/** A published page or post (or a preview of a draft). */
export function EntryView({ e, countries: list }: { e: Entry; countries: { code: string; name: string }[] }) {
  const content = e.content as {
    title: string;
    blocks?: { type: string; [k: string]: unknown }[];
    body?: string;
    excerpt?: string;
    cover_id?: string;
    author?: string;
    tags?: string[];
  };
  const media = e.media as Record<string, { url: string; alt: string; width: number; height: number }>;
  const banner = e.preview ? (
    <p className="bg-warn-bg px-4 py-2 text-center text-sm text-warn">Preview of an unpublished draft. Visitors don&apos;t see this.</p>
  ) : null;
  if (e.kind === "post") {
    const cover = content.cover_id ? media[content.cover_id] : undefined;
    return (
      <>
        {banner}
        <article className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
          <p className="text-sm text-muted">
            {e.published_at ? new Date(e.published_at).toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" }) : "Draft"}
            {content.author ? ` · ${content.author}` : ""}
          </p>
          <h1 className="mt-2 font-display text-4xl font-semibold tracking-tight text-ink">{content.title}</h1>
          {content.excerpt ? <p className="mt-4 text-xl text-muted">{content.excerpt}</p> : null}
          {cover ? <img src={cover.url} alt={cover.alt} width={cover.width} height={cover.height} className="mt-8 w-full rounded-2xl" /> : null}
          <Markdown source={content.body ?? ""} className="mt-8 text-lg text-ink" />
          {content.tags?.length ? (
            <p className="mt-10 flex flex-wrap gap-2">
              {content.tags.map((t) => (
                <a key={t} href={`/blog?tag=${encodeURIComponent(t)}`} className="rounded-full bg-surface-2 px-3 py-1 text-sm text-ink hover:bg-tint">
                  {t}
                </a>
              ))}
            </p>
          ) : null}
        </article>
      </>
    );
  }
  return (
    <>
      {banner}
      <Blocks blocks={content.blocks ?? []} ctx={{ media, locale: e.locale, posts: e.posts, countries: list }} />
    </>
  );
}
