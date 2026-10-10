"use client";

import { connectRealtime, ok, type RealtimeStatus } from "@diyneco/api-client";
import { Badge, Button, ErrorNotice, Spinner, ToastProvider } from "@diyneco/shared-ui";
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";

import { cookApi, deviceApi, whenCookSessionEnds } from "./api";
import { Board } from "./Board";
import { API_URL } from "./config";
import { appVersion, cookSession, credential, DeviceRevoked, getDeviceToken } from "./device";
import { PairScreen } from "./PairScreen";
import { SignInPanel } from "./SignInPanel";

type Mode = "loading" | "unpaired" | "board" | "locked" | "disabled" | "suspended";

export function KitchenApp() {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 5_000 } },
      }),
  );
  return (
    <QueryClientProvider client={client}>
      <ToastProvider>
        <Shell />
      </ToastProvider>
    </QueryClientProvider>
  );
}

function Shell() {
  const [mode, setMode] = useState<Mode>("loading");

  useEffect(() => {
    if (!credential.get()) {
      setMode("unpaired");
      return;
    }
    getDeviceToken()
      .then((t) => setMode(t ? "board" : "unpaired"))
      .catch((err) => setMode(err instanceof DeviceRevoked ? "unpaired" : "board"));
  }, []);

  if (mode === "loading") {
    return (
      <main className="flex min-h-dvh items-center justify-center">
        <Spinner className="size-8 text-muted" />
      </main>
    );
  }
  if (mode === "unpaired") return <PairScreen onPaired={() => setMode("board")} />;
  if (mode === "locked" || mode === "disabled" || mode === "suspended") {
    const text = {
      locked: "This display is locked by a manager.",
      disabled: "This display was turned off by a manager.",
      suspended: "Service is paused for this hotel. Please contact your manager.",
    }[mode];
    return (
      <main className="kds flex min-h-dvh flex-col items-center justify-center gap-4 p-8 text-center">
        <h1 className="font-display text-3xl font-semibold text-ink">{text}</h1>
        <p className="text-muted">The board comes back by itself once it is unlocked.</p>
        <Heartbeat onStatus={setMode} />
      </main>
    );
  }
  return <Kitchen onStatus={setMode} />;
}

/** Reports to the server every minute and applies its commands (RESET, LOCK). */
function Heartbeat({ onStatus }: { onStatus: (m: Mode) => void }) {
  useEffect(() => {
    let done: string[] = [];
    const beat = async () => {
      try {
        await getDeviceToken();
        const res = await ok(
          deviceApi.POST("/api/v1/devices/heartbeat", { body: { app_version: appVersion, completed_commands: done as never } }),
        );
        done = [];
        if (res.commands.includes("RESET")) {
          cookSession.clear();
          done.push("RESET");
        }
        onStatus(res.status === "locked" ? "locked" : res.status === "disabled" ? "disabled" : "board");
      } catch (err) {
        if (err instanceof DeviceRevoked) onStatus("unpaired");
        const code = (err as { code?: string }).code;
        if (code === "DEVICE_DISABLED") onStatus("disabled");
        if (code === "HOTEL_SUSPENDED") onStatus("suspended");
      }
    };
    void beat();
    const t = setInterval(beat, 60_000);
    return () => clearInterval(t);
  }, [onStatus]);
  return null;
}

function chime(): void {
  try {
    const ctx = new AudioContext();
    const tone = (freq: number, at: number) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.0001, ctx.currentTime + at);
      gain.gain.exponentialRampToValueAtTime(0.4, ctx.currentTime + at + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + at + 0.35);
      osc.connect(gain).connect(ctx.destination);
      osc.start(ctx.currentTime + at);
      osc.stop(ctx.currentTime + at + 0.4);
    };
    tone(880, 0);
    tone(1175, 0.18);
  } catch {
    /* audio blocked until the first touch */
  }
}

function Kitchen({ onStatus }: { onStatus: (m: Mode) => void }) {
  const qc = useQueryClient();
  const [live, setLive] = useState<RealtimeStatus>("connecting");
  const [cook, setCook] = useState(() => cookSession.get());
  const [signInOpen, setSignInOpen] = useState(false);
  const pending = useRef<(() => void) | null>(null);
  const [highVis, setHighVis] = useState(false);
  const [sound, setSound] = useState(true);
  const soundRef = useRef(sound);
  soundRef.current = sound;

  useEffect(() => {
    document.documentElement.dataset.contrast = highVis ? "high" : "";
  }, [highVis]);

  useEffect(() => {
    whenCookSessionEnds(() => setCook(null));
  }, []);

  const board = useQuery({
    queryKey: ["board"],
    queryFn: async () => {
      await getDeviceToken();
      return ok(deviceApi.GET("/api/v1/kitchen/orders"));
    },
    // The socket drives updates; polling covers a dropped connection (every 10 s) and is a
    // slow safety net otherwise.
    refetchInterval: live === "live" ? 60_000 : 10_000,
  });

  useEffect(() => {
    const rt = connectRealtime({
      baseUrl: API_URL,
      getToken: () => getDeviceToken(),
      onEvent: (event) => {
        if (event.type === "NEW_ORDER" && soundRef.current) chime();
        void qc.invalidateQueries({ queryKey: ["board"] });
      },
      onStatus: setLive,
      onFatal: (code) => onStatus(code === 4410 ? "suspended" : "unpaired"),
    });
    return () => rt.close();
  }, [qc, onStatus]);

  const needCook = useCallback(
    (action: () => void) => {
      if (cookSession.get()) action();
      else {
        pending.current = action;
        setSignInOpen(true);
      }
    },
    [],
  );

  const signOut = async () => {
    cookSession.clear();
    setCook(null);
    await cookApi.POST("/api/v1/auth/logout").catch(() => undefined);
  };

  const orders = board.data?.data ?? [];
  return (
    <main className="kds flex h-dvh flex-col gap-4 bg-bg p-4 lg:p-6">
      <Heartbeat onStatus={onStatus} />
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="font-display text-xl font-semibold text-ink">Kitchen</h1>
          <Badge tone={live === "live" ? "good" : live === "connecting" ? "info" : "warn"} className="text-sm">
            {live === "live" ? "Live" : live === "connecting" ? "Connecting…" : "Offline, refreshing every 10 s"}
          </Badge>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {cook ? (
            <>
              <span className="text-sm text-muted">
                Signed in: <strong className="text-ink">{cook.name}</strong>
              </span>
              <Button variant="secondary" size="lg" onClick={() => setSignInOpen(true)}>
                Switch cook
              </Button>
              <Button variant="ghost" size="lg" onClick={signOut}>
                Sign out
              </Button>
            </>
          ) : (
            <Button size="lg" onClick={() => setSignInOpen(true)}>
              Sign in with PIN
            </Button>
          )}
          <Button variant="secondary" size="lg" aria-pressed={sound} onClick={() => setSound(!sound)}>
            {sound ? "Sound on" : "Sound off"}
          </Button>
          <Button variant="secondary" size="lg" aria-pressed={highVis} onClick={() => setHighVis(!highVis)}>
            High visibility
          </Button>
          <Button
            variant="secondary"
            size="lg"
            onClick={() => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen())}
          >
            Full screen
          </Button>
        </div>
      </header>
      {board.error ? <ErrorNotice error={board.error} /> : null}
      {board.isLoading ? (
        <div className="flex flex-1 items-center justify-center">
          <Spinner className="size-8 text-muted" />
        </div>
      ) : (
        <Board orders={orders} needCook={needCook} />
      )}
      <SignInPanel
        open={signInOpen}
        onClose={() => {
          pending.current = null;
          setSignInOpen(false);
        }}
        onSignedIn={() => {
          setCook(cookSession.get());
          setSignInOpen(false);
          const action = pending.current;
          pending.current = null;
          action?.();
        }}
      />
    </main>
  );
}
