import type { Metadata } from "next";

import { legalDocuments } from "@/api";
import { LEGAL_KINDS } from "@/legal";

// Every current legal document from Admin > Legal documents.

export const revalidate = 300;

export const metadata: Metadata = { title: "Legal", alternates: { canonical: "/legal" } };

export default async function Page({ searchParams }: { searchParams: Promise<{ country?: string }> }) {
  const { country } = await searchParams;
  const docs = await legalDocuments(country && /^[A-Z]{2}$/.test(country) ? country : undefined);
  return (
    <section className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <h1 className="font-display text-4xl font-semibold tracking-tight text-ink">Legal</h1>
      <p className="mt-3 text-muted">The current version of each document. Where a country has its own version, it applies to properties there.</p>
      {docs.length === 0 ? (
        <p className="mt-10 text-muted">No documents are published yet.</p>
      ) : (
        <ul className="mt-10 divide-y divide-line rounded-[var(--radius-card)] border border-line bg-surface">
          {docs.map((d) => (
            <li key={d.id}>
              <a href={`/legal/${d.kind}${d.country ? `?country=${d.country}` : ""}`} className="flex items-center justify-between gap-4 p-5 hover:bg-surface-2">
                <span>
                  <span className="font-medium text-ink">{d.title}</span>
                  <span className="block text-sm text-muted">
                    {LEGAL_KINDS[d.kind] ?? d.kind}
                    {d.country ? ` · ${d.country}` : ""} · version {d.version}
                    {d.effective_at ? ` · in force from ${new Date(d.effective_at).toLocaleDateString()}` : ""}
                  </span>
                </span>
                <span aria-hidden className="text-muted">›</span>
              </a>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
