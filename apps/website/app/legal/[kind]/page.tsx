import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { legalDocuments } from "@/api";
import { LEGAL_KINDS } from "@/legal";
import { Markdown } from "@/markdown";

// One legal document, exactly as published in Admin > Legal documents: the country's own
// version where there is one (?country=ZA), otherwise the general one.

export const revalidate = 300;

type Props = { params: Promise<{ kind: string }>; searchParams: Promise<{ country?: string }> };

async function find(kind: string, country?: string) {
  const code = country && /^[A-Z]{2}$/.test(country) ? country : undefined;
  const docs = await legalDocuments(code);
  return docs.find((d) => d.kind === kind) ?? null;
}

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { kind } = await params;
  const doc = await find(kind, (await searchParams).country);
  return doc ? { title: doc.title, alternates: { canonical: `/legal/${kind}` } } : { title: LEGAL_KINDS[kind] ?? "Legal" };
}

export default async function Page({ params, searchParams }: Props) {
  const { kind } = await params;
  if (!LEGAL_KINDS[kind]) notFound();
  const doc = await find(kind, (await searchParams).country);
  if (!doc) {
    return (
      <section className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
        <h1 className="font-display text-4xl font-semibold text-ink">{LEGAL_KINDS[kind]}</h1>
        <p className="mt-6 text-muted">This document is not published yet. <a href="/contact" className="text-blue hover:underline">Contact us</a> for a copy.</p>
      </section>
    );
  }
  return (
    <article className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <p className="text-sm text-muted">
        <a href="/legal" className="hover:text-blue">Legal</a> › {LEGAL_KINDS[kind]}
      </p>
      <h1 className="mt-2 font-display text-4xl font-semibold tracking-tight text-ink">{doc.title}</h1>
      <p className="mt-3 text-sm text-muted">
        Version {doc.version}
        {doc.country ? ` · applies in ${doc.country}` : ""}
        {doc.effective_at ? ` · in force from ${new Date(doc.effective_at).toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" })}` : ""}
      </p>
      {doc.summary ? <p className="mt-6 rounded-lg bg-tint p-4 text-ink">{doc.summary}</p> : null}
      <Markdown source={doc.body ?? ""} className="mt-8 text-ink" />
    </article>
  );
}
