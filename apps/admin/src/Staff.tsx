"use client";

import { formatDate, ok } from "@diyneco/api-client";
import { Badge, Button, Card, Dialog, EmptyState, ErrorNotice, Field, Input, PageHeader, Skeleton, Table, Td, Th } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useAction } from "./common";
import { useMe, useSession } from "./session";

// Diyneco staff accounts (DECISIONS D71). Every change is confirmed with a password step-up
// and audited; nobody changes or deactivates their own account, and the database keeps at
// least one active Super Admin.

interface Member {
  id: string;
  email: string;
  name: string;
  status: "invited" | "active" | "locked" | "deactivated";
  roles: string[];
  mfa_enrolled: boolean;
  last_login_at: string | null;
  created_at: string;
}

interface PlatformRole {
  code: string;
  name: string;
  permissions: string[];
}

const STATUS: Record<Member["status"], ["good" | "warn" | "crit" | "neutral", string]> = {
  active: ["good", "Active"],
  invited: ["warn", "Invited"],
  locked: ["crit", "Locked"],
  deactivated: ["neutral", "Deactivated"],
};

export function Staff() {
  const { api } = useSession();
  const me = useMe().me;
  const staff = useQuery({ queryKey: ["platform-staff"], queryFn: () => ok(api.GET("/api/v1/admin/staff")) });
  const roles = useQuery({ queryKey: ["platform-roles"], queryFn: () => ok(api.GET("/api/v1/admin/staff/roles")) });
  const [editing, setEditing] = useState<Member | "new" | null>(null);
  const path = (id: string) => ({ params: { path: { user_id: id } } });
  const resend = useAction((id: string) => ok(api.POST("/api/v1/admin/staff/{user_id}/resend-invitation", path(id))), {
    success: "Invitation sent again. Earlier links no longer work.",
  });
  const deactivate = useAction((id: string) => ok(api.POST("/api/v1/admin/staff/{user_id}/deactivate", path(id))), {
    success: "Deactivated and signed out everywhere.",
  });
  const reactivate = useAction((id: string) => ok(api.POST("/api/v1/admin/staff/{user_id}/reactivate", path(id))), {
    success: (m) => ((m as Member).status === "invited" ? "Reactivated. A new invitation was sent." : "Reactivated."),
  });
  const rows = (staff.data?.data ?? []) as Member[];
  const roleList = (roles.data?.data ?? []) as PlatformRole[];
  const roleName = (code: string) => roleList.find((r) => r.code === code)?.name ?? code;
  const error = resend.error ?? deactivate.error ?? reactivate.error;

  return (
    <>
      <PageHeader
        title="Diyneco staff"
        description="Accounts for the admin panel. Each person signs in with a password and two-step sign-in."
        actions={<Button onClick={() => setEditing("new")}>Invite</Button>}
      />
      {error ? <ErrorNotice error={error} className="mb-4" /> : null}
      <Card>
        {staff.isLoading ? (
          <Skeleton className="h-40" />
        ) : staff.error ? (
          <ErrorNotice error={staff.error} />
        ) : rows.length ? (
          <Table>
            <thead>
              <tr>
                <Th>Person</Th>
                <Th>Roles</Th>
                <Th>Status</Th>
                <Th>Last sign-in</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {rows.map((m) => {
                const self = m.id === me.user?.id;
                return (
                  <tr key={m.id}>
                    <Td>
                      <p className="font-medium">
                        {m.name} {self ? <span className="text-xs text-muted">(you)</span> : null}
                      </p>
                      <p className="text-xs text-muted">{m.email}</p>
                    </Td>
                    <Td>{m.roles.map(roleName).join(", ") || "–"}</Td>
                    <Td>
                      <div className="flex flex-wrap gap-1">
                        <Badge tone={STATUS[m.status][0]}>{STATUS[m.status][1]}</Badge>
                        {m.status === "active" && !m.mfa_enrolled ? <Badge tone="warn">No two-step yet</Badge> : null}
                      </div>
                    </Td>
                    <Td>{m.last_login_at ? formatDate(m.last_login_at) : "Never"}</Td>
                    <Td className="text-right">
                      {self ? null : (
                        <div className="flex justify-end gap-2">
                          {m.status === "invited" ? (
                            <Button size="sm" variant="secondary" loading={resend.isPending} onClick={() => resend.mutate(m.id)}>
                              Resend
                            </Button>
                          ) : null}
                          {m.status === "deactivated" ? (
                            <Button size="sm" variant="secondary" loading={reactivate.isPending} onClick={() => reactivate.mutate(m.id)}>
                              Reactivate
                            </Button>
                          ) : (
                            <>
                              <Button size="sm" variant="secondary" onClick={() => setEditing(m)}>
                                Roles
                              </Button>
                              <Button size="sm" variant="secondary" loading={deactivate.isPending} onClick={() => deactivate.mutate(m.id)}>
                                Deactivate
                              </Button>
                            </>
                          )}
                        </div>
                      )}
                    </Td>
                  </tr>
                );
              })}
            </tbody>
          </Table>
        ) : (
          <EmptyState title="No staff accounts" body="Invite the people who run the platform." />
        )}
      </Card>
      {editing ? (
        <StaffDialog member={editing === "new" ? null : editing} roles={roleList} onClose={() => setEditing(null)} />
      ) : null}
    </>
  );
}

function StaffDialog({ member, roles, onClose }: { member: Member | null; roles: PlatformRole[]; onClose: () => void }) {
  const { api } = useSession();
  const [f, setF] = useState({ name: "", email: "" });
  const [picked, setPicked] = useState<string[]>(member?.roles ?? []);
  const save = useAction(
    () =>
      member
        ? ok(
            api.PUT("/api/v1/admin/staff/{user_id}/roles", {
              params: { path: { user_id: member.id } },
              body: { roles: picked },
            }),
          )
        : ok(api.POST("/api/v1/admin/staff", { body: { name: f.name, email: f.email, roles: picked } })),
    { success: member ? "Roles changed. They apply at once." : "Invitation sent. The link works for 72 hours.", onDone: onClose },
  );
  const toggle = (code: string) => setPicked(picked.includes(code) ? picked.filter((c) => c !== code) : [...picked, code]);
  return (
    <Dialog
      open
      onClose={onClose}
      title={member ? `Roles of ${member.name}` : "Invite a staff member"}
      description={member ? "Changes apply on their next request." : "They get an email to choose a password."}
      footer={
        <Button
          loading={save.isPending}
          disabled={!picked.length || (!member && (!f.name.trim() || !f.email.includes("@")))}
          onClick={() => save.mutate(undefined)}
        >
          {member ? "Save roles" : "Send invitation"}
        </Button>
      }
    >
      <div className="flex flex-col gap-3">
        {member ? null : (
          <>
            <Field label="Name">{(p) => <Input {...p} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />}</Field>
            <Field label="Work email" hint="Not an address already used by a hotel account.">
              {(p) => <Input {...p} type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} />}
            </Field>
          </>
        )}
        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1 text-sm font-medium text-ink">Roles</legend>
          {roles.map((r) => (
            <label key={r.code} className="flex items-start gap-3 rounded-md border border-line p-3 text-sm">
              <input type="checkbox" className="mt-1" checked={picked.includes(r.code)} onChange={() => toggle(r.code)} />
              <span>
                <span className="font-medium text-ink">{r.name}</span>
                <span className="block text-xs text-muted">{r.permissions.join(", ")}</span>
              </span>
            </label>
          ))}
        </fieldset>
        {save.error ? <ErrorNotice error={save.error} /> : null}
      </div>
    </Dialog>
  );
}
