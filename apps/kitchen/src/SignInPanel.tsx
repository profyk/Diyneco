"use client";

import { ok } from "@diyneco/api-client";
import { Button, Dialog, ErrorNotice, Spinner } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { deviceApi } from "./api";
import { cookSession } from "./device";

const PAD = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0", "⌫"];

/** Pick your name, enter your PIN. Every action on the board is then recorded against you. */
export function SignInPanel({ open, onClose, onSignedIn }: { open: boolean; onClose: () => void; onSignedIn: () => void }) {
  const [userId, setUserId] = useState<string | null>(null);
  const [pin, setPin] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const staff = useQuery({
    queryKey: ["kitchen-staff"],
    queryFn: () => ok(deviceApi.GET("/api/v1/kitchen/staff")),
    enabled: open,
  });
  const chosen = staff.data?.data.find((s) => s.user_id === userId);

  const reset = () => {
    setUserId(null);
    setPin("");
    setError(null);
  };

  const signIn = async (value: string) => {
    if (!userId) return;
    setBusy(true);
    setError(null);
    try {
      const s = await ok(
        deviceApi.POST("/api/v1/auth/kitchen/sign-in", { body: { user_id: userId, pin: value } }),
      );
      cookSession.set({
        token: s.access_token,
        userId: s.user.id,
        name: s.user.name,
        expiresAt: Date.now() + s.expires_in * 1000,
      });
      reset();
      onSignedIn();
    } catch (err) {
      setError(err);
      setPin("");
    } finally {
      setBusy(false);
    }
  };

  const press = (k: string) => {
    setError(null);
    if (k === "⌫") return setPin((p) => p.slice(0, -1));
    const next = (pin + k).slice(0, 6);
    setPin(next);
  };

  return (
    <Dialog
      open={open}
      onClose={() => {
        reset();
        onClose();
      }}
      size="lg"
      title={chosen ? `Hi ${chosen.name.split(" ")[0]}, enter your PIN` : "Who is working?"}
      description={chosen ? "Your PIN signs this display in for 8 hours." : "Choose your name."}
    >
      {!chosen ? (
        staff.isLoading ? (
          <div className="flex justify-center py-10">
            <Spinner />
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {staff.data?.data.map((s) => (
              <Button key={s.user_id} variant="secondary" size="xl" onClick={() => setUserId(s.user_id)}>
                {s.name}
              </Button>
            ))}
            {staff.data?.data.length === 0 ? (
              <p className="col-span-full text-muted">No kitchen staff have a PIN yet. A manager can set one in Staff.</p>
            ) : null}
          </div>
        )
      ) : (
        <div className="mx-auto max-w-sm">
          <div className="mb-4 flex justify-center gap-3" aria-live="polite">
            {Array.from({ length: Math.max(4, pin.length) }, (_, i) => (
              <span key={i} className={`size-4 rounded-full ${i < pin.length ? "bg-ink" : "border-2 border-line"}`} />
            ))}
          </div>
          {error ? <ErrorNotice error={error} className="mb-4" /> : null}
          <div className="grid grid-cols-3 gap-3">
            {PAD.map((k, i) =>
              k ? (
                <Button key={i} variant="secondary" size="xl" onClick={() => press(k)} disabled={busy} aria-label={k === "⌫" ? "Delete" : k}>
                  {k}
                </Button>
              ) : (
                <span key={i} />
              ),
            )}
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <Button variant="ghost" size="lg" onClick={reset}>
              Not me
            </Button>
            <Button size="lg" disabled={pin.length < 4} loading={busy} onClick={() => signIn(pin)}>
              Sign in
            </Button>
          </div>
        </div>
      )}
    </Dialog>
  );
}
