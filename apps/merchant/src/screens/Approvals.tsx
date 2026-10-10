"use client";

import { elapsed, formatMoney, formatTime, ok } from "@diyneco/api-client";
import {
  Button,
  Card,
  CardHeader,
  Dialog,
  EmptyState,
  ErrorNotice,
  Field,
  PageHeader,
  Skeleton,
  Table,
  Td,
  Textarea,
  Th,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { useAction } from "../common";
import { useMe, useSession } from "../session";

export function Approvals() {
  const { api, can } = useSession();
  const { me } = useMe();
  const orders = useQuery({
    queryKey: ["orders", "pending"],
    queryFn: () => ok(api.GET("/api/v1/orders", { params: { query: { status: "PENDING_APPROVAL", limit: 200 } } })),
    enabled: can("orders.approve"),
  });
  const adjustments = useQuery({
    queryKey: ["adjustments", "pending"],
    queryFn: () => ok(api.GET("/api/v1/adjustments", { params: { query: { status: "pending" } } })),
    enabled: can("folio.adjust.approve"),
  });
  const [rejecting, setRejecting] = useState<string | null>(null);

  const approveOrder = useAction(
    (id: string) => ok(api.POST("/api/v1/orders/{order_id}/approve", { params: { path: { order_id: id } } })),
    { success: "Approved and sent to the kitchen." },
  );
  const approveAdjustment = useAction(
    (id: string) =>
      ok(api.POST("/api/v1/adjustments/{adjustment_id}/approve", { params: { path: { adjustment_id: id } } })),
    { success: "Adjustment approved; the bill is corrected." },
  );

  return (
    <>
      <PageHeader
        title="Approvals"
        description="Orders over the room-charge limit and bill adjustments wait here. Approving asks for your PIN."
      />
      {approveOrder.error || approveAdjustment.error ? (
        <ErrorNotice error={approveOrder.error ?? approveAdjustment.error} className="mb-4" />
      ) : null}
      {can("orders.approve") ? (
        <Card className="mb-6">
          <CardHeader title="Orders over the limit" description="Declining needs a reason the guest will see." />
          {orders.isLoading ? (
            <Skeleton className="m-5 h-10" />
          ) : orders.data?.data.length ? (
            <Table>
              <thead>
                <tr>
                  <Th>Order</Th>
                  <Th>Room</Th>
                  <Th>Waiting</Th>
                  <Th className="text-right">Total</Th>
                  <Th />
                </tr>
              </thead>
              <tbody>
                {orders.data.data.map((o) => (
                  <tr key={o.id}>
                    <Td>
                      <Link className="font-mono text-blue hover:underline" href={`/orders?open=${o.id}`}>
                        #{o.number}
                      </Link>
                    </Td>
                    <Td>{o.room}</Td>
                    <Td className="text-muted">{elapsed(o.created_at)}</Td>
                    <Td className="text-right tabular-nums">{formatMoney(o.total)}</Td>
                    <Td className="text-right">
                      <Button size="sm" loading={approveOrder.isPending} onClick={() => approveOrder.mutate(o.id)}>
                        Approve
                      </Button>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          ) : (
            <EmptyState title="No orders waiting" />
          )}
        </Card>
      ) : null}
      {can("folio.adjust.approve") ? (
        <Card>
          <CardHeader
            title="Bill adjustments"
            description="Two people are always involved: you cannot approve a change you asked for."
          />
          {adjustments.isLoading ? (
            <Skeleton className="m-5 h-10" />
          ) : adjustments.data?.data.length ? (
            <Table>
              <thead>
                <tr>
                  <Th>Room</Th>
                  <Th>Change</Th>
                  <Th>Reason</Th>
                  <Th>Asked by</Th>
                  <Th />
                </tr>
              </thead>
              <tbody>
                {adjustments.data.data.map((a) => {
                  const mine = a.requested_by === me.user?.id;
                  return (
                    <tr key={a.id}>
                      <Td>
                        <Link className="text-blue hover:underline" href={`/stays/${a.stay_id}`}>
                          {a.room}
                        </Link>
                      </Td>
                      <Td className="tabular-nums">
                        {formatMoney(a.original)} → <strong>{formatMoney(a.new_amount)}</strong>
                      </Td>
                      <Td className="max-w-64 truncate" title={a.reason}>
                        {a.reason}
                      </Td>
                      <Td className="text-muted">
                        {a.requested_by_name} · {formatTime(a.requested_at)}
                      </Td>
                      <Td className="whitespace-nowrap text-right">
                        {mine ? (
                          <span className="text-xs text-muted">Needs another manager</span>
                        ) : (
                          <div className="flex justify-end gap-2">
                            <Button size="sm" variant="secondary" onClick={() => setRejecting(a.id)}>
                              Reject
                            </Button>
                            <Button
                              size="sm"
                              loading={approveAdjustment.isPending}
                              onClick={() => approveAdjustment.mutate(a.id)}
                            >
                              Approve
                            </Button>
                          </div>
                        )}
                      </Td>
                    </tr>
                  );
                })}
              </tbody>
            </Table>
          ) : (
            <EmptyState title="No adjustments waiting" />
          )}
        </Card>
      ) : null}
      {rejecting ? <RejectDialog id={rejecting} onClose={() => setRejecting(null)} /> : null}
    </>
  );
}

function RejectDialog({ id, onClose }: { id: string; onClose: () => void }) {
  const { api } = useSession();
  const [reason, setReason] = useState("");
  const reject = useAction(
    () =>
      ok(
        api.POST("/api/v1/adjustments/{adjustment_id}/reject", {
          params: { path: { adjustment_id: id } },
          body: { reason },
        }),
      ),
    { success: "Adjustment rejected.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      size="sm"
      title="Reject adjustment"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Back
          </Button>
          <Button variant="danger" disabled={!reason.trim()} loading={reject.isPending} onClick={() => reject.mutate(undefined)}>
            Reject
          </Button>
        </>
      }
    >
      <Field label="Reason">{(p) => <Textarea {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}</Field>
      {reject.error ? <ErrorNotice error={reject.error} className="mt-3" /> : null}
    </Dialog>
  );
}
