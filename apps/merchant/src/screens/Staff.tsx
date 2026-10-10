"use client";

import { formatDate, ok } from "@diyneco/api-client";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  Dialog,
  EmptyState,
  ErrorNotice,
  Field,
  Input,
  PageHeader,
  Skeleton,
  Table,
  Td,
  Th,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useAction } from "../common";
import { useMe, useSession } from "../session";

export function Staff() {
  const { api, can } = useSession();
  const { me } = useMe();
  const [inviting, setInviting] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const staff = useQuery({ queryKey: ["staff"], queryFn: () => ok(api.GET("/api/v1/staff")) });
  const invites = useQuery({
    queryKey: ["invitations"],
    queryFn: () => ok(api.GET("/api/v1/staff/invitations")),
    enabled: can("staff.manage"),
  });
  const cancelInvite = useAction(
    (id: string) => ok(api.DELETE("/api/v1/staff/invitations/{invitation_id}", { params: { path: { invitation_id: id } } })),
    { success: "Invitation cancelled." },
  );
  const resetPin = useAction(
    (id: string) => ok(api.POST("/api/v1/staff/{user_id}/pin/reset", { params: { path: { user_id: id } } })),
    { success: "PIN cleared. They set a new one at their next sign-in." },
  );
  const deactivate = useAction(
    (id: string) => ok(api.POST("/api/v1/staff/{user_id}/deactivate", { params: { path: { user_id: id } } })),
    { success: "Access removed. Their sessions ended." },
  );
  const error = cancelInvite.error ?? resetPin.error ?? deactivate.error;

  return (
    <>
      <PageHeader
        title="Staff"
        description="Everyone signs in as themselves; roles decide what they can do."
        actions={can("staff.manage") ? <Button onClick={() => setInviting(true)}>Invite someone</Button> : null}
      />
      {error ? <ErrorNotice error={error} className="mb-4" /> : null}
      <Card>
        {staff.isLoading ? (
          <Skeleton className="m-5 h-10" />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Name</Th>
                <Th>Roles</Th>
                <Th>Security</Th>
                <Th>Last sign-in</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {staff.data?.data.map((s) => (
                <tr key={s.user_id} className={s.status !== "active" ? "opacity-60" : undefined}>
                  <Td>
                    <p className="font-medium">{s.name}</p>
                    <p className="text-xs text-muted">{s.email}</p>
                  </Td>
                  <Td>
                    <div className="flex flex-wrap gap-1">
                      {s.roles.map((r) => (
                        <Badge key={r.id}>{r.name}</Badge>
                      ))}
                    </div>
                  </Td>
                  <Td>
                    <div className="flex flex-wrap gap-1">
                      <Badge tone={s.mfa_enabled ? "good" : "neutral"}>{s.mfa_enabled ? "Two-step on" : "Password only"}</Badge>
                      <Badge tone={s.has_pin ? "good" : "warn"}>{s.has_pin ? "PIN set" : "No PIN"}</Badge>
                    </div>
                  </Td>
                  <Td className="text-muted">{s.last_sign_in_at ? formatDate(s.last_sign_in_at) : "Never"}</Td>
                  <Td className="whitespace-nowrap text-right">
                    {can("staff.manage") && s.status === "active" && s.user_id !== me.user?.id ? (
                      <div className="flex justify-end gap-1">
                        <Button size="sm" variant="secondary" onClick={() => setEditing(s.user_id)}>
                          Roles
                        </Button>
                        {s.has_pin ? (
                          <Button size="sm" variant="ghost" onClick={() => resetPin.mutate(s.user_id)}>
                            Reset PIN
                          </Button>
                        ) : null}
                        <Button size="sm" variant="ghost" onClick={() => deactivate.mutate(s.user_id)}>
                          Remove
                        </Button>
                      </div>
                    ) : s.status !== "active" ? (
                      <Badge tone="neutral">Removed</Badge>
                    ) : null}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
      {can("staff.manage") && invites.data?.data.length ? (
        <Card className="mt-6">
          <CardHeader title="Waiting invitations" description="Each invitation holds a seat on your plan until it is accepted or expires." />
          <Table>
            <tbody>
              {invites.data.data.map((i) => (
                <tr key={i.id}>
                  <Td>
                    <p className="font-medium">{i.name}</p>
                    <p className="text-xs text-muted">{i.email}</p>
                  </Td>
                  <Td>{i.roles.map((r) => r.name).join(", ")}</Td>
                  <Td className="text-muted">Expires {formatDate(i.expires_at)}</Td>
                  <Td className="text-right">
                    <Button size="sm" variant="ghost" onClick={() => cancelInvite.mutate(i.id)}>
                      Cancel
                    </Button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      ) : null}
      {inviting ? <InviteDialog onClose={() => setInviting(false)} /> : null}
      {editing ? (
        <RolesDialog
          userId={editing}
          current={staff.data?.data.find((s) => s.user_id === editing)?.roles.map((r) => r.id) ?? []}
          onClose={() => setEditing(null)}
        />
      ) : null}
    </>
  );
}

function RolePicker({ value, onChange }: { value: string[]; onChange: (ids: string[]) => void }) {
  const { api } = useSession();
  const roles = useQuery({ queryKey: ["roles"], queryFn: () => ok(api.GET("/api/v1/roles")) });
  if (!roles.data) return <Skeleton />;
  return (
    <fieldset className="grid gap-2 sm:grid-cols-2">
      <legend className="mb-2 text-sm font-medium text-ink">Roles</legend>
      {roles.data.data.map((r) => (
        <label key={r.id} className="flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm">
          <input
            type="checkbox"
            checked={value.includes(r.id)}
            onChange={(e) => onChange(e.target.checked ? [...value, r.id] : value.filter((x) => x !== r.id))}
          />
          {r.name}
          {!r.is_system ? <span className="text-xs text-muted">(custom)</span> : null}
        </label>
      ))}
    </fieldset>
  );
}

function InviteDialog({ onClose }: { onClose: () => void }) {
  const { api } = useSession();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [department, setDepartment] = useState("");
  const [roleIds, setRoleIds] = useState<string[]>([]);
  const send = useAction(
    () =>
      ok(
        api.POST("/api/v1/staff/invitations", {
          body: { name: name.trim(), email: email.trim(), department: department.trim() || null, role_ids: roleIds },
        }),
      ),
    { success: "Invitation sent. It is valid for 7 days.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title="Invite someone"
      description="They get an email to set their password. Some roles must also turn on two-step sign-in."
      footer={
        <Button disabled={!name.trim() || !email.trim() || roleIds.length === 0} loading={send.isPending} onClick={() => send.mutate(undefined)}>
          Send invitation
        </Button>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Name">{(p) => <Input {...p} value={name} onChange={(e) => setName(e.target.value)} />}</Field>
        <Field label="Email">{(p) => <Input {...p} type="email" value={email} onChange={(e) => setEmail(e.target.value)} />}</Field>
        <Field label="Department (optional)" className="sm:col-span-2">
          {(p) => <Input {...p} value={department} onChange={(e) => setDepartment(e.target.value)} />}
        </Field>
      </div>
      <div className="mt-4">
        <RolePicker value={roleIds} onChange={setRoleIds} />
      </div>
      {send.error ? <ErrorNotice error={send.error} className="mt-4" /> : null}
    </Dialog>
  );
}

function RolesDialog({ userId, current, onClose }: { userId: string; current: string[]; onClose: () => void }) {
  const { api } = useSession();
  const [roleIds, setRoleIds] = useState<string[]>(current);
  const save = useAction(
    () => ok(api.PUT("/api/v1/staff/{user_id}/roles", { params: { path: { user_id: userId } }, body: { role_ids: roleIds } })),
    { success: "Roles updated. Their access changes immediately.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title="Change roles"
      description="You can only give access you hold yourself. Asks for your PIN."
      footer={
        <Button disabled={roleIds.length === 0} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Save
        </Button>
      }
    >
      <RolePicker value={roleIds} onChange={setRoleIds} />
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
      {roleIds.length === 0 ? <EmptyState title="Choose at least one role" /> : null}
    </Dialog>
  );
}
