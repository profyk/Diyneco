/**
 * A small, safe Markdown renderer for posts, rich-text blocks and legal documents. It builds
 * React elements and never injects HTML, so content can't run scripts. Supported: headings
 * (#, ##, ###), paragraphs, bullet and numbered lists, block quotes, horizontal rules,
 * **bold**, *italic*, `code` and [links](https://...) to https, mailto or site paths.
 */
import type { ReactNode } from "react";

const SAFE_HREF = /^(https:\/\/|mailto:|\/(?!\/))/;

function inline(text: string, key: string): ReactNode[] {
  const out: ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|_[^_]+_|`[^`]+`|\[[^\]]+\]\([^)\s]+\))/g;
  let last = 0;
  let i = 0;
  for (const m of text.matchAll(re)) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const t = m[0];
    const k = `${key}-${i++}`;
    if (t.startsWith("**")) out.push(<strong key={k}>{t.slice(2, -2)}</strong>);
    else if (t.startsWith("`")) out.push(<code key={k} className="rounded bg-surface-2 px-1 py-0.5 font-mono text-[0.9em]">{t.slice(1, -1)}</code>);
    else if (t.startsWith("[")) {
      const label = t.slice(1, t.indexOf("]"));
      const href = t.slice(t.indexOf("(") + 1, -1);
      out.push(
        SAFE_HREF.test(href) ? (
          <a key={k} href={href} className="text-blue underline-offset-2 hover:underline" {...(href.startsWith("https://") ? { rel: "noopener noreferrer" } : {})}>
            {label}
          </a>
        ) : (
          label
        ),
      );
    } else out.push(<em key={k}>{t.slice(1, -1)}</em>);
    last = m.index + t.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

export function Markdown({ source, className }: { source: string; className?: string }) {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let para: string[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;
  let quote: string[] = [];

  const flush = () => {
    const k = `b${blocks.length}`;
    if (para.length) {
      blocks.push(
        <p key={k} className="my-4 leading-7">
          {inline(para.join(" "), k)}
        </p>,
      );
      para = [];
    }
    if (list) {
      const items = list.items.map((it, i) => (
        <li key={i} className="my-1">
          {inline(it, `${k}-${i}`)}
        </li>
      ));
      blocks.push(
        list.ordered ? (
          <ol key={`${k}l`} className="my-4 list-decimal pl-6">
            {items}
          </ol>
        ) : (
          <ul key={`${k}l`} className="my-4 list-disc pl-6">
            {items}
          </ul>
        ),
      );
      list = null;
    }
    if (quote.length) {
      blocks.push(
        <blockquote key={`${k}q`} className="my-4 border-l-4 border-line pl-4 text-muted">
          {inline(quote.join(" "), `${k}q`)}
        </blockquote>,
      );
      quote = [];
    }
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const heading = /^(#{1,3})\s+(.*)$/.exec(line);
    const bullet = /^\s*[-*]\s+(.*)$/.exec(line);
    const numbered = /^\s*\d+[.)]\s+(.*)$/.exec(line);
    if (!line.trim()) {
      flush();
    } else if (heading) {
      flush();
      const level = heading[1]?.length ?? 1;
      const text = heading[2] ?? "";
      const k = `h${blocks.length}`;
      blocks.push(
        level === 1 ? (
          <h2 key={k} className="mt-10 mb-3 font-display text-2xl font-semibold text-ink">{inline(text, k)}</h2>
        ) : level === 2 ? (
          <h3 key={k} className="mt-8 mb-2 font-display text-xl font-semibold text-ink">{inline(text, k)}</h3>
        ) : (
          <h4 key={k} className="mt-6 mb-2 text-base font-semibold text-ink">{inline(text, k)}</h4>
        ),
      );
    } else if (/^(-{3,}|\*{3,})$/.test(line.trim())) {
      flush();
      blocks.push(<hr key={`r${blocks.length}`} className="my-8 border-line" />);
    } else if (bullet || numbered) {
      if (para.length || quote.length || (list && list.ordered !== Boolean(numbered))) {
        const keep = list && list.ordered === Boolean(numbered) ? list : null;
        if (!keep) flush();
      }
      list = list ?? { ordered: Boolean(numbered), items: [] };
      list.items.push((bullet?.[1] ?? numbered?.[1] ?? "").trim());
    } else if (line.startsWith(">")) {
      if (para.length || list) flush();
      quote.push(line.replace(/^>\s?/, ""));
    } else {
      if (list || quote.length) flush();
      para.push(line.trim());
    }
  }
  flush();
  return <div className={className}>{blocks}</div>;
}
