"use client";

// Where a payment page sends the hotel back (DECISIONS D79). Arriving here proves nothing: the
// page asks the API, which asks the provider, and shows what the provider reports. A sandbox
// checkout (test mode, never in production) is finished here by an explicit choice.

import { formatMoney, ok } from "@diyneco/api-client";
import { Badge, Button, Card, ErrorNotice, PageHeader, Spinner } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useState } from "react";

import { useAction } from "../common";
import { useSession } from "../session";

const MESSAGES: Record<string, string> = {
  succeeded: "Payment received. Thank you.",
  failed: "The payment did not go through. Nothing was charged.",
  cancelled: "The payment was cancelled. Nothing was charged.",
  expired: "The payment page expired. Nothing was charged.",
};

export function PaymentReturn() {
  const { api, can } = useSession();
  const [params, setParams] = useState<{ attempt: string | null; sandbox: boolean } | null>(null);
  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    setParams({ attempt: q.get("attempt"), sandbox: q.get("sandbox") === "1" });
  }, []);
  const attemptId = params?.attempt ?? null;
  const attempt = useQuery({
    queryKey: ["payment-attempt", attemptId],
    enabled: !!attemptId && /^[0-9a-f-]{36}$/i.test(attemptId),
    queryFn: () => ok(api.GET("/api/v1/subscription/payment-attempts/{attempt_id}", { params: { path: { attempt_id: attemptId ?? "" } } })),
    // A provider may take a moment to confirm; keep asking while it is pending (not in the sandbox).
    refetchInterval: (q) => (q.state.data?.status === "pending" && !params?.sandbox ? 3000 : false),
  });
  const finish = useAction(
    (outcome: "succeeded" | "failed") =>
      ok(
        api.POST("/api/v1/subscription/payment-attempts/{attempt_id}/sandbox", {
          params: { path: { attempt_id: attemptId ?? "" } },
          body: { outcome },
        }),
      ),
    {},
  );
  const a = attempt.data;
  return (
    <>
      <PageHeader title="Payment" />
      <Card className="max-w-xl p-6">
        {!params ? (
          <Spinner />
        ) : !attemptId ? (
          <p className="text-sm">There is no payment to show.</p>
        ) : attempt.isError ? (
          <ErrorNotice error={attempt.error} />
        ) : !a ? (
          <Spinner />
        ) : a.status === "pending" && a.provider === "sandbox" ? (
          <>
            <p className="rounded bg-warn/15 px-3 py-2 text-sm font-semibold uppercase tracking-wide">Test mode: no real money moves</p>
            <p className="mt-4 text-sm">
              This is Diyneco&apos;s payment sandbox, used until a payment provider is connected. Choose what the test payment of{" "}
              <strong>{formatMoney(a.amount)}</strong> should do. It is recorded as a test payment and never counted as money received.
            </p>
            {can("subscription.manage") ? (
              <div className="mt-5 flex flex-wrap gap-3">
                <Button loading={finish.isPending} onClick={() => finish.mutate("succeeded")}>
                  Simulate a successful payment
                </Button>
                <Button variant="secondary" loading={finish.isPending} onClick={() => finish.mutate("failed")}>
                  Simulate a failed payment
                </Button>
              </div>
            ) : null}
            {finish.error ? <ErrorNotice error={finish.error} className="mt-3" /> : null}
          </>
        ) : a.status === "pending" ? (
          <div className="flex items-center gap-3 text-sm">
            <Spinner /> Waiting for {a.provider_label} to confirm the payment…
          </div>
        ) : (
          <>
            <p className="text-lg font-semibold">
              {MESSAGES[a.status]} {a.test_mode ? <Badge tone="warn">Test</Badge> : null}
            </p>
            <p className="mt-1 text-sm text-muted">
              {formatMoney(a.amount)} · {a.provider_label}
              {a.failure_reason ? ` · ${a.failure_reason}` : ""}
            </p>
          </>
        )}
        <Link href="/settings?tab=plan" className="mt-6 inline-block text-sm text-blue underline">
          Back to your plan and invoices
        </Link>
      </Card>
    </>
  );
}
