import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { countries, preview } from "@/api";
import { EntryView } from "@/EntryView";

// A draft opened from Admin > Website (a 15-minute link). Never cached, never indexed.

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Preview", robots: { index: false, follow: false } };

export default async function Page({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token } = await searchParams;
  const e = token ? await preview(token) : null;
  if (!e) notFound();
  return <EntryView e={e} countries={await countries()} />;
}
