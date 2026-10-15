/**
 * Renders the typed blocks of a page (D83). The API validates every block, so only these
 * types with bounded text ever arrive. Images come from the API's media store.
 */
import type { ReactNode } from "react";

import { type Entry, MERCHANT_URL, plans } from "./api";
import { GalleryGrid } from "./Gallery";
import { LeadForm } from "./LeadForm";
import { Markdown } from "./markdown";
import { PricingTable } from "./Pricing";

type Media = Record<string, { url: string; src?: Record<string, string>; alt: string; width: number; height: number }>;
type Cta = { label: string; href: string };
type Block = { type: string; [k: string]: unknown };

export interface BlockContext {
  media: Media;
  locale: string;
  posts: Entry["posts"];
  countries: { code: string; name: string }[];
}

function Img({ id, media, className, sizes = "100vw" }: { id?: unknown; media: Media; className?: string; sizes?: string }) {
  const m = typeof id === "string" ? media[id] : undefined;
  if (!m) return null;
  const srcSet = m.src ? Object.entries(m.src).map(([w, u]) => `${u} ${w}w`).join(", ") : undefined;
  return <img src={m.url} srcSet={srcSet} sizes={sizes} alt={m.alt} width={m.width} height={m.height} loading="lazy" className={className} />;
}

function href(h: string): string {
  // "/signup" and "/sign-in" go to the Merchant app; other links stay on the site.
  if (h === "/signup" || h.startsWith("/signup?")) return `${MERCHANT_URL}${h}`;
  if (h === "/sign-in") return `${MERCHANT_URL}/`;
  return h;
}

function Button({ cta, primary }: { cta?: Cta | null; primary?: boolean }) {
  if (!cta) return null;
  return (
    <a
      href={href(cta.href)}
      className={
        primary
          ? "inline-flex h-12 items-center rounded-[10px] bg-brand px-6 font-medium text-on-brand hover:opacity-90"
          : "inline-flex h-12 items-center rounded-[10px] border border-line bg-surface px-6 font-medium text-ink hover:bg-surface-2"
      }
    >
      {cta.label}
    </a>
  );
}

function Section({ children, tint = false }: { children: ReactNode; tint?: boolean }) {
  return (
    <section className={tint ? "bg-surface-2" : ""}>
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">{children}</div>
    </section>
  );
}

function Heading({ text, intro }: { text?: unknown; intro?: unknown }) {
  if (!text && !intro) return null;
  return (
    <div className="mx-auto mb-10 max-w-2xl text-center">
      {text ? <h2 className="font-display text-3xl font-semibold tracking-tight text-ink">{String(text)}</h2> : null}
      {intro ? <p className="mt-3 text-lg text-muted">{String(intro)}</p> : null}
    </div>
  );
}

async function render(b: Block, i: number, ctx: BlockContext): Promise<ReactNode> {
  switch (b.type) {
    case "hero":
      return (
        <section key={i} className="bg-gradient-to-b from-tint to-bg">
          <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-20 sm:px-6 lg:grid-cols-2 lg:py-28">
            <div>
              {b.eyebrow ? <p className="text-sm font-semibold uppercase tracking-wide text-blue">{String(b.eyebrow)}</p> : null}
              <h1 className="mt-3 font-display text-4xl font-semibold tracking-tight text-ink sm:text-5xl">{String(b.heading)}</h1>
              {b.subheading ? <p className="mt-5 text-lg text-muted">{String(b.subheading)}</p> : null}
              <div className="mt-8 flex flex-wrap gap-3">
                <Button cta={b.primary as Cta} primary />
                <Button cta={b.secondary as Cta} />
              </div>
            </div>
            <Img id={b.image_id} media={ctx.media} sizes="(min-width: 1024px) 50vw, 100vw" className="w-full rounded-2xl shadow-xl" />
          </div>
        </section>
      );
    case "features": {
      const items = (b.items as { title: string; body: string; image_id?: string }[]) ?? [];
      return (
        <Section key={i}>
          <Heading text={b.heading} intro={b.intro} />
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((it) => (
              <div key={it.title} className="overflow-hidden rounded-[var(--radius-card)] border border-line bg-surface">
                <Img id={it.image_id} media={ctx.media} sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw" className="aspect-[16/10] w-full object-cover" />
                <div className="p-6">
                  <h3 className="font-display text-lg font-semibold text-ink">{it.title}</h3>
                  <p className="mt-2 text-muted">{it.body}</p>
                </div>
              </div>
            ))}
          </div>
        </Section>
      );
    }
    case "steps": {
      const items = (b.items as { title: string; body: string }[]) ?? [];
      return (
        <Section key={i} tint>
          <Heading text={b.heading} />
          <ol className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {items.map((it, n) => (
              <li key={it.title} className="rounded-[var(--radius-card)] bg-surface p-6">
                <span className="flex size-9 items-center justify-center rounded-full bg-brand font-semibold text-on-brand">{n + 1}</span>
                <h3 className="mt-4 font-semibold text-ink">{it.title}</h3>
                <p className="mt-1 text-sm text-muted">{it.body}</p>
              </li>
            ))}
          </ol>
        </Section>
      );
    }
    case "split":
      return (
        <Section key={i}>
          <div className={`grid items-center gap-10 lg:grid-cols-2 ${b.image_side === "left" ? "lg:[&>*:first-child]:order-2" : ""}`}>
            <div>
              <h2 className="font-display text-3xl font-semibold tracking-tight text-ink">{String(b.heading)}</h2>
              <Markdown source={String(b.body ?? "")} className="mt-2 text-lg text-muted" />
              <div className="mt-6">
                <Button cta={b.cta as Cta} primary />
              </div>
            </div>
            <Img id={b.image_id} media={ctx.media} sizes="(min-width: 1024px) 50vw, 100vw" className="w-full rounded-2xl" />
          </div>
        </Section>
      );
    case "stats": {
      const items = (b.items as { value: string; label: string }[]) ?? [];
      return (
        <Section key={i} tint>
          <Heading text={b.heading} />
          <dl className="grid gap-6 text-center sm:grid-cols-2 lg:grid-cols-4">
            {items.map((it) => (
              <div key={it.label}>
                <dt className="text-sm text-muted">{it.label}</dt>
                <dd className="mt-1 font-display text-4xl font-semibold text-ink">{it.value}</dd>
              </div>
            ))}
          </dl>
        </Section>
      );
    }
    case "testimonials": {
      const items = (b.items as { quote: string; name: string; role?: string; hotel?: string }[]) ?? [];
      return (
        <Section key={i}>
          <Heading text={b.heading} />
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {items.map((t) => (
              <figure key={t.name + t.quote.slice(0, 20)} className="rounded-[var(--radius-card)] border border-line bg-surface p-6">
                <blockquote className="text-ink">“{t.quote}”</blockquote>
                <figcaption className="mt-4 text-sm text-muted">
                  <span className="font-medium text-ink">{t.name}</span>
                  {[t.role, t.hotel].filter(Boolean).length ? ` · ${[t.role, t.hotel].filter(Boolean).join(", ")}` : ""}
                </figcaption>
              </figure>
            ))}
          </div>
        </Section>
      );
    }
    case "faq": {
      const items = (b.items as { question: string; answer: string }[]) ?? [];
      return (
        <Section key={i}>
          <Heading text={b.heading ?? "Questions"} />
          <div className="mx-auto max-w-3xl divide-y divide-line rounded-[var(--radius-card)] border border-line bg-surface">
            {items.map((q) => (
              <details key={q.question} className="group p-5">
                <summary className="cursor-pointer list-none font-medium text-ink">
                  <span className="mr-2 inline-block transition group-open:rotate-90">›</span>
                  {q.question}
                </summary>
                <Markdown source={q.answer} className="mt-2 pl-5 text-muted" />
              </details>
            ))}
          </div>
        </Section>
      );
    }
    case "cta":
      return (
        <section key={i} className="bg-brand">
          <div className="mx-auto max-w-4xl px-4 py-16 text-center sm:px-6">
            <h2 className="font-display text-3xl font-semibold text-on-brand">{String(b.heading)}</h2>
            {b.body ? <p className="mt-3 text-lg text-on-brand/80">{String(b.body)}</p> : null}
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <a href={href((b.primary as Cta).href)} className="inline-flex h-12 items-center rounded-[10px] bg-white px-6 font-medium text-brand hover:opacity-90">
                {(b.primary as Cta).label}
              </a>
              {b.secondary ? (
                <a href={href((b.secondary as Cta).href)} className="inline-flex h-12 items-center rounded-[10px] border border-white/40 px-6 font-medium text-on-brand hover:bg-white/10">
                  {(b.secondary as Cta).label}
                </a>
              ) : null}
            </div>
          </div>
        </section>
      );
    case "logos": {
      const items = (b.items as { image_id: string; name: string; href?: string }[]) ?? [];
      return (
        <Section key={i}>
          <Heading text={b.heading} />
          <div className="flex flex-wrap items-center justify-center gap-10 opacity-80">
            {items.map((l) => (
              <Img key={l.image_id} id={l.image_id} media={ctx.media} sizes="160px" className="h-10 w-auto" />
            ))}
          </div>
        </Section>
      );
    }
    case "pricing":
      return (
        <Section key={i}>
          <Heading text={b.heading ?? "Simple pricing"} intro={b.intro} />
          <PricingTable plans={await plans()} signupUrl={`${MERCHANT_URL}/signup`} />
        </Section>
      );
    case "rich_text":
      return (
        <Section key={i}>
          <Markdown source={String(b.body ?? "")} className="mx-auto max-w-3xl text-ink" />
        </Section>
      );
    case "lead_form":
      return (
        <Section key={i} tint>
          <div className="mx-auto max-w-3xl">
            <LeadForm
              kind={b.kind === "demo" ? "demo" : "contact"}
              heading={b.heading as string}
              intro={b.intro as string}
              locale={ctx.locale}
              countries={ctx.countries}
            />
          </div>
        </Section>
      );
    case "gallery": {
      const items = (b.items as { image_id: string; caption?: string | null; category?: string }[]) ?? [];
      const photos = items
        .map((it) => {
          const m = ctx.media[it.image_id];
          if (!m) return null;
          return {
            url: m.url,
            srcSet: m.src ? Object.entries(m.src).map(([w, u]) => `${u} ${w}w`).join(", ") : undefined,
            alt: m.alt || it.caption || "",
            width: m.width,
            height: m.height,
            caption: it.caption,
            category: it.category ?? "other",
          };
        })
        .filter((p) => p !== null);
      return (
        <Section key={i}>
          <Heading text={b.heading} intro={b.intro} />
          <GalleryGrid photos={photos} showFilters={b.show_filters !== false} />
        </Section>
      );
    }
    case "post_list":
      return (
        <Section key={i}>
          <Heading text={b.heading ?? "From the blog"} />
          <PostGrid posts={(ctx.posts ?? []).slice(0, Number(b.limit ?? 3))} />
        </Section>
      );
    default:
      return null;
  }
}

export async function Blocks({ blocks, ctx }: { blocks: Block[]; ctx: BlockContext }) {
  return <>{await Promise.all(blocks.map((b, i) => render(b, i, ctx)))}</>;
}

type Card = { path: string; title: string; excerpt?: string | null; cover?: { [key: string]: unknown } | null; published_at: string };

export function PostGrid({ posts }: { posts: { [key: string]: unknown }[] }) {
  const cards = posts as unknown as Card[];
  if (!cards.length) return <p className="text-center text-muted">No posts yet.</p>;
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {cards.map((p) => (
        <a key={p.path} href={p.path} className="group overflow-hidden rounded-[var(--radius-card)] border border-line bg-surface">
          {p.cover ? (
            <img src={String(p.cover.url)} alt={String(p.cover.alt ?? "")} loading="lazy" className="aspect-[16/9] w-full object-cover" />
          ) : null}
          <div className="p-5">
            <p className="text-xs text-muted">{new Date(p.published_at).toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" })}</p>
            <h3 className="mt-1 font-display text-lg font-semibold text-ink group-hover:text-blue">{p.title}</h3>
            {p.excerpt ? <p className="mt-2 text-sm text-muted">{p.excerpt}</p> : null}
          </div>
        </a>
      ))}
    </div>
  );
}
