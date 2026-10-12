"use client";

import { formatDate, ok } from "@diyneco/api-client";
import {
  Badge,
  Button,
  Card,
  Dialog,
  EmptyState,
  ErrorNotice,
  Field,
  Input,
  PageHeader,
  Select,
  Skeleton,
  Table,
  Td,
  Textarea,
  Th,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useAction } from "./common";
import { useSession } from "./session";

// Legal documents (DECISIONS D70): drafts are edited here, published versions are frozen.

type Kind = "terms" | "privacy" | "dpa" | "acceptable_use" | "guest_terms" | "guest_privacy";

const KINDS: [Kind, string][] = [
  ["terms", "Terms of service"],
  ["privacy", "Privacy notice"],
  ["dpa", "Data processing agreement"],
  ["acceptable_use", "Acceptable use policy"],
  ["guest_terms", "Guest terms (tablet)"],
  ["guest_privacy", "Guest privacy notice (tablet)"],
];
const kindName = (k: string) => KINDS.find(([v]) => v === k)?.[1] ?? k;

interface LegalDoc {
  id: string;
  kind: Kind;
  country: string | null;
  version: number;
  title: string;
  summary: string | null;
  status: "draft" | "published";
  published_at: string | null;
  body?: string | null;
}

export function Legal() {
  const { api } = useSession();
  const docs = useQuery({ queryKey: ["legal"], queryFn: () => ok(api.GET("/api/v1/admin/legal-documents")) });
  const [editing, setEditing] = useState<LegalDoc | "new" | null>(null);
  const publish = useAction(
    (id: string) =>
      ok(api.POST("/api/v1/admin/legal-documents/{document_id}/publish", { params: { path: { document_id: id } } })),
    { success: "Published. Merchants are asked to accept it the next time they open the app." },
  );
  const remove = useAction(
    (id: string) =>
      ok(api.DELETE("/api/v1/admin/legal-documents/{document_id}", { params: { path: { document_id: id } } })),
    { success: "Draft deleted." },
  );
  const rows = (docs.data?.data ?? []) as LegalDoc[];
  return (
    <>
      <PageHeader
        title="Legal documents"
        description="Published versions are frozen. To change one, create the next version and publish it."
        actions={<Button onClick={() => setEditing("new")}>New version</Button>}
      />
      {publish.error || remove.error ? <ErrorNotice error={publish.error ?? remove.error} className="mb-4" /> : null}
      <Card>
        {docs.isLoading ? (
          <Skeleton className="h-40" />
        ) : rows.length ? (
          <Table>
            <thead>
              <tr>
                <Th>Document</Th>
                <Th>Country</Th>
                <Th>Version</Th>
                <Th>Status</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {rows.map((d) => (
                <tr key={d.id}>
                  <Td>
                    <p className="font-medium">{d.title}</p>
                    <p className="text-xs text-muted">{kindName(d.kind)}</p>
                  </Td>
                  <Td>{d.country ?? "Everywhere"}</Td>
                  <Td>v{d.version}</Td>
                  <Td>
                    {d.status === "published" ? (
                      <Badge tone="good">Published {d.published_at ? formatDate(d.published_at) : ""}</Badge>
                    ) : (
                      <Badge tone="warn">Draft</Badge>
                    )}
                  </Td>
                  <Td className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button size="sm" variant="secondary" onClick={() => setEditing(d)}>
                        {d.status === "draft" ? "Edit" : "View"}
                      </Button>
                      {d.status === "draft" ? (
                        <>
                          <Button size="sm" variant="secondary" onClick={() => remove.mutate(d.id)}>
                            Delete
                          </Button>
                          <Button size="sm" loading={publish.isPending} onClick={() => publish.mutate(d.id)}>
                            Publish
                          </Button>
                        </>
                      ) : null}
                    </div>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        ) : (
          <EmptyState
            title="No legal documents yet"
            body="Signup asks for acceptance once terms, a privacy notice and a DPA are published."
          />
        )}
      </Card>
      {editing ? <LegalDialog doc={editing === "new" ? null : editing} onClose={() => setEditing(null)} /> : null}
    </>
  );
}

function LegalDialog({ doc, onClose }: { doc: LegalDoc | null; onClose: () => void }) {
  const { api } = useSession();
  // The admin list carries the text; published versions can also be read from the public endpoint.
  const [f, setF] = useState({
    kind: doc?.kind ?? ("terms" as Kind),
    country: doc?.country ?? "",
    title: doc?.title ?? "",
    summary: doc?.summary ?? "",
    body: doc?.body ?? "",
  });
  const readOnly = doc?.status === "published";
  const save = useAction(
    () =>
      doc
        ? ok(
            api.PATCH("/api/v1/admin/legal-documents/{document_id}", {
              params: { path: { document_id: doc.id } },
              body: { title: f.title, body: f.body, summary: f.summary || null },
            }),
          )
        : ok(
            api.POST("/api/v1/admin/legal-documents", {
              body: { kind: f.kind, country: f.country || null, title: f.title, body: f.body, summary: f.summary || null },
            }),
          ),
    { success: "Draft saved.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title={doc ? `${doc.title} · v${doc.version}` : "New version"}
      description={readOnly ? "Published: this version can no longer change." : "Drafts are visible only here until published."}
      footer={
        readOnly ? null : (
          <Button loading={save.isPending} disabled={!f.title || !f.body} onClick={() => save.mutate(undefined)}>
            Save draft
          </Button>
        )
      }
    >
      <div className="flex flex-col gap-3">
        {!doc ? (
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Document">
              {(p) => (
                <Select {...p} value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value as Kind })}>
                  {KINDS.map(([k, n]) => (
                    <option key={k} value={k}>
                      {n}
                    </option>
                  ))}
                </Select>
              )}
            </Field>
            <Field label="Country" hint="Two letters, e.g. GB. Leave empty for every country without its own version.">
              {(p) => (
                <Input
                  {...p}
                  maxLength={2}
                  value={f.country}
                  onChange={(e) => setF({ ...f, country: e.target.value.toUpperCase().replace(/[^A-Z]/g, "") })}
                />
              )}
            </Field>
          </div>
        ) : null}
        <Field label="Title">
          {(p) => <Input {...p} disabled={readOnly} value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} />}
        </Field>
        <Field label="What changed" hint="Shown to people when they are asked to accept.">
          {(p) => <Input {...p} disabled={readOnly} value={f.summary} onChange={(e) => setF({ ...f, summary: e.target.value })} />}
        </Field>
        <Field label="Text">
          {(p) => <Textarea {...p} rows={16} disabled={readOnly} value={f.body} onChange={(e) => setF({ ...f, body: e.target.value })} />}
        </Field>
        {save.error ? <ErrorNotice error={save.error} /> : null}
      </div>
    </Dialog>
  );
}
