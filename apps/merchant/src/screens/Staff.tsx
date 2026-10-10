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
  const [profile, setProfile] = useState<{ id: string; name: string; department: string | null } | null>(null);
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
                    <p className="text-xs text-muted">
                      {s.email}
                      {s.department ? ` · ${s.department}` : ""}
                    </p>
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
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setProfile({ id: s.user_id, name: s.name, department: s.department })}
                        >
                          Edit
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
      {can("roles.manage") || can("staff.read") ? <Roles /> : null}
      {inviting ? <InviteDialog onClose={() => setInviting(false)} /> : null}
      {profile ? <ProfileDialog person={profile} onClose={() => setProfile(null)} /> : null}
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

function ProfileDialog({ person, onClose }: { person: { id: string; name: string; department: string | null }; onClose: () => void }) {
  const { api } = useSession();
  const [name, setName] = useState(person.name);
  const [department, setDepartment] = useState(person.department ?? "");
  const save = useAction(
    () =>
      ok(
        api.PATCH("/api/v1/staff/{user_id}", {
          params: { path: { user_id: person.id } },
          body: { name: name.trim(), department: department.trim() || null },
        }),
      ),
    { success: "Saved.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      title={`Edit ${person.name}`}
      footer={
        <Button disabled={!name.trim()} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Save
        </Button>
      }
    >
      <div className="grid gap-4">
        <Field label="Name">{(p) => <Input {...p} value={name} onChange={(e) => setName(e.target.value)} />}</Field>
        <Field label="Department" hint="For example Front office, Kitchen, Housekeeping.">
          {(p) => <Input {...p} value={department} onChange={(e) => setDepartment(e.target.value)} />}
        </Field>
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}

const AREA_NAMES: Record<string, string> = {
  hotel: "Hotel",
  settings: "Settings",
  rooms: "Rooms",
  devices: "Devices",
  staff: "Staff",
  roles: "Roles",
  guests: "Guests",
  privacy: "Privacy",
  billing: "Company billing",
  stays: "Stays",
  menu: "Menu",
  kitchen: "Kitchen",
  orders: "Orders",
  deliveries: "Room service",
  folio: "Bills",
  payments: "Payments",
  invoices: "Invoices",
  checkout: "Checkout",
  reports: "Reports",
  audit: "Audit",
  integrations: "Integrations",
  subscription: "Subscription",
};

/** System roles are fixed; a hotel can add its own roles from the same permissions. */
function Roles() {
  const { api, can } = useSession();
  const [editing, setEditing] = useState<{ id: string | null } | null>(null);
  const roles = useQuery({ queryKey: ["roles"], queryFn: () => ok(api.GET("/api/v1/roles")) });
  return (
    <Card className="mt-6">
      <CardHeader
        title="Roles"
        description="What each role can do. Built-in roles follow Diyneco's permission matrix; add your own for other jobs."
        actions={can("roles.manage") ? <Button onClick={() => setEditing({ id: null })}>New role</Button> : undefined}
      />
      <ul className="divide-y divide-line">
        {roles.data?.data.map((r) => (
          <li key={r.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
            <div className="min-w-0">
              <p className="font-medium text-ink">
                {r.name} {r.is_system ? <Badge>Built in</Badge> : <Badge tone="teal">Custom</Badge>}
              </p>
              <p className="text-sm text-muted">{r.permissions.length} permissions</p>
            </div>
            <Button size="sm" variant="ghost" onClick={() => setEditing({ id: r.id })}>
              {r.is_system || !can("roles.manage") ? "View" : "Edit"}
            </Button>
          </li>
        ))}
      </ul>
      {editing ? (
        <RoleEditor role={editing.id ? roles.data?.data.find((r) => r.id === editing.id) ?? null : null} onClose={() => setEditing(null)} />
      ) : null}
    </Card>
  );
}

function RoleEditor({
  role,
  onClose,
}: {
  role: { id: string; name: string; is_system: boolean; permissions: string[] } | null;
  onClose: () => void;
}) {
  const { api, can } = useSession();
  const readOnly = Boolean(role?.is_system) || !can("roles.manage");
  const perms = useQuery({ queryKey: ["permissions"], queryFn: () => ok(api.GET("/api/v1/permissions")) });
  const [name, setName] = useState(role?.name ?? "");
  const [chosen, setChosen] = useState<string[]>(role?.permissions ?? []);
  const save = useAction(
    () =>
      role
        ? ok(api.PATCH("/api/v1/roles/{role_id}", { params: { path: { role_id: role.id } }, body: { name: name.trim(), permissions: chosen } }))
        : ok(api.POST("/api/v1/roles", { body: { name: name.trim(), permissions: chosen } })),
    { success: role ? "Role saved. People with it get the change at their next request." : "Role created.", onDone: onClose },
  );
  const areas = (perms.data?.data ?? []).reduce<Record<string, { code: string; description: string; sensitive: boolean }[]>>((acc, p) => {
    const area = p.code.split(".")[0]!;
    (acc[area] ??= []).push(p);
    return acc;
  }, {});
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title={role ? role.name : "New role"}
      description={
        readOnly
          ? "Built-in roles cannot be changed. Create a custom role to give a different set."
          : "You can only give permissions you hold yourself. Marked permissions are sensitive and need a PIN when used."
      }
      footer={
        readOnly ? undefined : (
          <Button disabled={!name.trim() || chosen.length === 0} loading={save.isPending} onClick={() => save.mutate(undefined)}>
            {role ? "Save role" : "Create role"}
          </Button>
        )
      }
    >
      {!readOnly ? (
        <Field label="Role name" className="mb-4">
          {(p) => <Input {...p} placeholder="Night auditor" value={name} onChange={(e) => setName(e.target.value)} />}
        </Field>
      ) : null}
      {perms.isLoading ? (
        <Skeleton className="h-40" />
      ) : (
        <div className="grid max-h-[55vh] gap-4 overflow-auto sm:grid-cols-2">
          {Object.entries(areas).map(([area, list]) => (
            <fieldset key={area} className="rounded-lg border border-line p-3">
              <legend className="px-1 text-sm font-semibold text-ink">{AREA_NAMES[area] ?? area}</legend>
              {list.map((p) => (
                <label key={p.code} className="flex items-start gap-2 py-1 text-sm text-ink">
                  <input
                    type="checkbox"
                    className="mt-1"
                    disabled={readOnly}
                    checked={chosen.includes(p.code)}
                    onChange={(e) => setChosen(e.target.checked ? [...chosen, p.code] : chosen.filter((c) => c !== p.code))}
                  />
                  <span>
                    {p.description}
                    {p.sensitive ? <Badge tone="warn" className="ml-1">PIN</Badge> : null}
                  </span>
                </label>
              ))}
            </fieldset>
          ))}
        </div>
      )}
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}
