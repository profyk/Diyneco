"use client";

import { ok } from "@diyneco/api-client";
import { Button, Card, ErrorNotice, Spinner } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";

import { useAction } from "./common";
import { API_URL } from "./config";
import { useSession } from "./session";

// Legal documents (DECISIONS D70). The API decides which versions are current; the app only
// shows them and sends back the ids the person accepted.

export interface LegalDoc {
  id: string;
  kind: string;
  version: number;
  title: string;
  summary: string | null;
  body?: string | null;
}

/** One document, collapsed to its title; the text opens in place. */
export function LegalText({ doc }: { doc: LegalDoc }) {
  const full = useQuery({
    queryKey: ["legal-doc", doc.id],
    enabled: doc.body == null,
    queryFn: async () => (await (await fetch(`${API_URL}/api/v1/legal/documents/${doc.id}`)).json()) as LegalDoc,
  });
  const body = doc.body ?? full.data?.body;
  return (
    <details className="rounded-lg border border-line p-3 text-sm">
      <summary className="cursor-pointer font-medium text-ink">
        {doc.title} <span className="text-muted">· version {doc.version}</span>
      </summary>
      {doc.summary ? <p className="mt-2 text-muted">What changed: {doc.summary}</p> : null}
      <div className="mt-2 max-h-72 overflow-y-auto whitespace-pre-wrap text-ink">{body ?? "Loading…"}</div>
    </details>
  );
}

/** Signed-in staff must accept new versions before using the app. */
export function LegalGate({ children }: { children: ReactNode }) {
  const { api, state, signOut } = useSession();
  const pending = useQuery({
    queryKey: ["legal-pending", state.status === "signed-in" ? state.me.hotel?.id : null],
    queryFn: () => ok(api.GET("/api/v1/legal/pending")),
    staleTime: 5 * 60_000,
  });
  const [agreed, setAgreed] = useState(false);
  const accept = useAction(
    (ids: string[]) => ok(api.POST("/api/v1/legal/accept", { body: { document_ids: ids } })),
    { success: "Thank you." },
  );
  if (pending.isLoading) {
    return (
      <main className="flex min-h-dvh items-center justify-center">
        <Spinner className="size-8 text-muted" />
      </main>
    );
  }
  const docs = (pending.data?.data ?? []) as LegalDoc[];
  if (!docs.length) return <>{children}</>;
  return (
    <main className="flex min-h-dvh items-center justify-center bg-bg p-4">
      <Card className="w-full max-w-2xl p-6">
        <h1 className="font-display text-2xl font-semibold text-ink">Updated terms</h1>
        <p className="mt-1 text-sm text-muted">Please read and accept these to keep using Diyneco.</p>
        <div className="mt-4 flex flex-col gap-2">
          {docs.map((d) => (
            <LegalText key={d.id} doc={d} />
          ))}
        </div>
        <label className="mt-4 flex items-center gap-2 text-sm text-ink">
          <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} />
          I have read and accept these documents.
        </label>
        {accept.error ? <ErrorNotice error={accept.error} className="mt-3" /> : null}
        <div className="mt-5 flex justify-between gap-2">
          <Button variant="secondary" onClick={() => void signOut()}>
            Sign out
          </Button>
          <Button disabled={!agreed} loading={accept.isPending} onClick={() => accept.mutate(docs.map((d) => d.id))}>
            Accept and continue
          </Button>
        </div>
      </Card>
    </main>
  );
}
