"use client";

import { formatTime, ok } from "@diyneco/api-client";
import {
  Badge,
  Button,
  Card,
  Dialog,
  EmptyState,
  ErrorNotice,
  Field,
  PageHeader,
  Select,
  Skeleton,
  Table,
  Td,
  Th,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { label, useAction } from "../common";
import { useSession } from "../session";

type DeviceAction = "lock" | "unlock" | "reset" | "disable";

export function Devices() {
  const { api, can } = useSession();
  const [pairing, setPairing] = useState(false);
  const [moving, setMoving] = useState<{ id: string; label: string } | null>(null);
  const devices = useQuery({
    queryKey: ["devices"],
    queryFn: () => ok(api.GET("/api/v1/devices", { params: { query: { limit: 200 } } })),
    refetchInterval: 30_000,
  });
  const act = useAction(
    ({ id, action }: { id: string; action: DeviceAction }) => {
      const path = `/api/v1/devices/{device_id}/${action}` as "/api/v1/devices/{device_id}/lock";
      return ok(api.POST(path, { params: { path: { device_id: id } } }));
    },
    { success: (d) => `${d.label}: ${label(d.status)}.` },
  );
  const unpair = useAction(
    (id: string) => ok(api.DELETE("/api/v1/devices/{device_id}/pairing", { params: { path: { device_id: id } } })),
    { success: "Device unpaired. Its credential no longer works." },
  );

  return (
    <>
      <PageHeader
        title="Devices"
        description="Room tablets and kitchen displays. A tablet belongs to one room; unpairing stops it at once."
        actions={can("devices.manage") ? <Button onClick={() => setPairing(true)}>Pair a device</Button> : null}
      />
      {act.error || unpair.error ? <ErrorNotice error={act.error ?? unpair.error} className="mb-4" /> : null}
      <Card>
        {devices.isLoading ? (
          <Skeleton className="m-5 h-10" />
        ) : !devices.data?.data.length ? (
          <EmptyState title="No devices yet" body="Pair a room tablet or a kitchen display with a 6-digit code." />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Device</Th>
                <Th>Where</Th>
                <Th>Connection</Th>
                <Th>Status</Th>
                <Th>Last seen</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {devices.data.data.map((d) => (
                <tr key={d.id}>
                  <Td>
                    <p className="font-medium">{d.label}</p>
                    <p className="text-xs text-muted">{d.kind === "guest" ? "Room tablet" : "Kitchen display"}</p>
                  </Td>
                  <Td>{d.room ? `Room ${d.room.number}` : d.stations.map((s) => s.name).join(", ") || "–"}</Td>
                  <Td>
                    <Badge tone={d.connection === "online" ? "good" : d.connection === "offline" ? "warn" : "neutral"}>
                      {label(d.connection)}
                    </Badge>
                  </Td>
                  <Td>
                    <Badge tone={d.status === "active" ? "good" : d.status === "locked" || d.status === "reset_required" ? "warn" : "crit"}>
                      {label(d.status)}
                    </Badge>
                  </Td>
                  <Td className="text-muted">{d.last_seen_at ? formatTime(d.last_seen_at) : "Never"}</Td>
                  <Td className="whitespace-nowrap text-right">
                    {can("devices.manage") && d.status !== "revoked" ? (
                      <div className="flex justify-end gap-1">
                        {d.status === "locked" ? (
                          <Button size="sm" variant="secondary" onClick={() => act.mutate({ id: d.id, action: "unlock" })}>
                            Unlock
                          </Button>
                        ) : (
                          <Button size="sm" variant="secondary" onClick={() => act.mutate({ id: d.id, action: "lock" })}>
                            Lock
                          </Button>
                        )}
                        {d.kind === "guest" ? (
                          <>
                            <Button size="sm" variant="secondary" onClick={() => act.mutate({ id: d.id, action: "reset" })}>
                              Reset
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => setMoving({ id: d.id, label: d.label })}>
                              Move
                            </Button>
                          </>
                        ) : null}
                        {d.status !== "disabled" ? (
                          <Button size="sm" variant="ghost" onClick={() => act.mutate({ id: d.id, action: "disable" })}>
                            Disable
                          </Button>
                        ) : null}
                        <Button size="sm" variant="ghost" onClick={() => unpair.mutate(d.id)}>
                          Unpair
                        </Button>
                      </div>
                    ) : null}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
      {pairing ? <PairDialog onClose={() => setPairing(false)} /> : null}
      {moving ? <MoveDialog device={moving} onClose={() => setMoving(null)} /> : null}
    </>
  );
}

function PairDialog({ onClose }: { onClose: () => void }) {
  const { api } = useSession();
  const [type, setType] = useState<"guest" | "kitchen">("guest");
  const [roomId, setRoomId] = useState("");
  const [stationId, setStationId] = useState("");
  const [now, setNow] = useState(Date.now());
  const rooms = useQuery({
    queryKey: ["rooms", "all"],
    queryFn: () => ok(api.GET("/api/v1/rooms", { params: { query: { limit: 200 } } })),
  });
  const stations = useQuery({ queryKey: ["stations"], queryFn: () => ok(api.GET("/api/v1/kitchen-stations")) });
  const create = useAction(() =>
    ok(
      api.POST("/api/v1/devices/pairings", {
        body: type === "guest" ? { type, room_id: roomId } : { type, station_ids: stationId ? [stationId] : [] },
      }),
    ),
  );
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  const code = create.data;
  const secondsLeft = code ? Math.max(0, Math.round((new Date(code.expires_at).getTime() - now) / 1000)) : 0;

  return (
    <Dialog open onClose={onClose} title="Pair a device" description="Open the Diyneco app on the device and enter the code.">
      {code && secondsLeft > 0 ? (
        <div className="text-center">
          <p className="font-mono text-5xl font-semibold tracking-[0.3em] text-ink">{code.code}</p>
          <p className="mt-3 text-sm text-muted">
            Valid for {Math.floor(secondsLeft / 60)}:{String(secondsLeft % 60).padStart(2, "0")}. It works once.
          </p>
          <Button className="mt-5" variant="secondary" onClick={onClose}>
            Done
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <Field label="Device">
            {(p) => (
              <Select {...p} value={type} onChange={(e) => setType(e.target.value as "guest" | "kitchen")}>
                <option value="guest">Room tablet</option>
                <option value="kitchen">Kitchen display</option>
              </Select>
            )}
          </Field>
          {type === "guest" ? (
            <Field label="Room">
              {(p) => (
                <Select {...p} value={roomId} onChange={(e) => setRoomId(e.target.value)}>
                  <option value="">Choose a room</option>
                  {rooms.data?.data.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.number}
                    </option>
                  ))}
                </Select>
              )}
            </Field>
          ) : (
            <Field label="Kitchen station">
              {(p) => (
                <Select {...p} value={stationId} onChange={(e) => setStationId(e.target.value)}>
                  <option value="">Choose a station</option>
                  {stations.data?.data.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </Select>
              )}
            </Field>
          )}
          {create.error ? <ErrorNotice error={create.error} /> : null}
          <Button
            disabled={type === "guest" ? !roomId : !stationId}
            loading={create.isPending}
            onClick={() => create.mutate(undefined)}
          >
            Create pairing code
          </Button>
        </div>
      )}
    </Dialog>
  );
}

/** Moves a room tablet to another room; it resets so the new room starts clean. */
function MoveDialog({ device, onClose }: { device: { id: string; label: string }; onClose: () => void }) {
  const { api } = useSession();
  const [roomId, setRoomId] = useState("");
  const rooms = useQuery({
    queryKey: ["rooms", "all"],
    queryFn: () => ok(api.GET("/api/v1/rooms", { params: { query: { limit: 200 } } })),
  });
  const move = useAction(
    () =>
      ok(api.POST("/api/v1/devices/{device_id}/reassign", { params: { path: { device_id: device.id } }, body: { room_id: roomId } })),
    { success: (d) => `${d.label} now belongs to room ${d.room?.number ?? ""}.`, onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      title={`Move ${device.label}`}
      description="The tablet resets and shows the new room's guest. Any open session on it ends."
      footer={
        <Button disabled={!roomId} loading={move.isPending} onClick={() => move.mutate(undefined)}>
          Move tablet
        </Button>
      }
    >
      <Field label="New room">
        {(p) => (
          <Select {...p} value={roomId} onChange={(e) => setRoomId(e.target.value)}>
            <option value="">Choose a room</option>
            {rooms.data?.data.map((r) => (
              <option key={r.id} value={r.id}>
                {r.number}
              </option>
            ))}
          </Select>
        )}
      </Field>
      {move.error ? <ErrorNotice error={move.error} className="mt-4" /> : null}
    </Dialog>
  );
}
