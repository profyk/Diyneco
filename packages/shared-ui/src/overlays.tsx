"use client";

import {
  createContext,
  type FormEvent,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { Button, cn, Field, Input } from "./primitives";

/** Modal dialog on the native <dialog> element: focus trap, Escape and backdrop for free. */
export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  size = "md",
}: {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  description?: ReactNode;
  children?: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg";
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    if (!open && el.open) el.close();
  }, [open]);
  const width = { sm: "max-w-sm", md: "max-w-lg", lg: "max-w-2xl" }[size];
  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      className={cn(
        "m-auto w-[calc(100%-2rem)] rounded-[var(--radius-card)] border border-line bg-surface p-0 text-ink shadow-2xl",
        "backdrop:bg-black/50",
        width,
      )}
    >
      {open ? (
        <div className="flex max-h-[85vh] flex-col">
          <div className="border-b border-line px-5 py-4">
            <h2 className="font-display text-lg font-semibold">{title}</h2>
            {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
          </div>
          <div className="overflow-y-auto px-5 py-4">{children}</div>
          {footer ? <div className="flex justify-end gap-2 border-t border-line px-5 py-3">{footer}</div> : null}
        </div>
      ) : null}
    </dialog>
  );
}

/** Shows what went wrong in the server's own words, with its request id for support. */
export function ErrorNotice({ error, className }: { error: unknown; className?: string }) {
  if (!error) return null;
  const e = error as { message?: string; requestId?: string | null; code?: string };
  return (
    <div role="alert" className={cn("rounded-[10px] border border-transparent bg-crit-bg px-4 py-3 text-sm text-crit", className)}>
      <p>{e.message ?? "Something went wrong."}</p>
      {e.requestId ? <p className="mt-1 font-mono text-xs opacity-80">Reference {e.requestId}</p> : null}
    </div>
  );
}

// --- Step-up (PIN or password before a sensitive action) -----------------------------------

type StepUpRequest = (secret: { pin?: string; password?: string }) => Promise<string>;

interface StepUpState {
  resolve: (token: string | null) => void;
}

const StepUpContext = createContext<(() => Promise<string | null>) | null>(null);

/**
 * Provides `useStepUp()`; the API client calls it when the server answers STEP_UP_REQUIRED.
 * `request` exchanges a PIN or password for a 5-minute step-up token (POST /auth/step-up).
 */
export function StepUpProvider({
  request,
  allowPassword = true,
  children,
}: {
  request: StepUpRequest;
  allowPassword?: boolean;
  children: ReactNode;
}) {
  const [pending, setPending] = useState<StepUpState | null>(null);
  const [mode, setMode] = useState<"pin" | "password">("pin");
  const [value, setValue] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const ask = useCallback(
    () =>
      new Promise<string | null>((resolve) => {
        setValue("");
        setError(null);
        setPending({ resolve });
      }),
    [],
  );

  const close = (token: string | null) => {
    pending?.resolve(token);
    setPending(null);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      close(await request(mode === "pin" ? { pin: value } : { password: value }));
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <StepUpContext.Provider value={ask}>
      {children}
      <Dialog
        open={pending !== null}
        onClose={() => close(null)}
        size="sm"
        title="Confirm it's you"
        description="This action needs your PIN. It stays confirmed for 5 minutes."
      >
        <form onSubmit={submit} className="flex flex-col gap-4">
          <Field label={mode === "pin" ? "PIN" : "Password"} error={error ? (error as Error).message : undefined}>
            {(props) => (
              <Input
                {...props}
                autoFocus
                type="password"
                inputMode={mode === "pin" ? "numeric" : "text"}
                autoComplete={mode === "pin" ? "off" : "current-password"}
                maxLength={mode === "pin" ? 8 : 200}
                value={value}
                onChange={(e) => setValue(e.target.value)}
              />
            )}
          </Field>
          <div className="flex items-center justify-between gap-2">
            {allowPassword ? (
              <button
                type="button"
                className="text-sm text-blue underline-offset-2 hover:underline"
                onClick={() => setMode(mode === "pin" ? "password" : "pin")}
              >
                Use {mode === "pin" ? "password" : "PIN"} instead
              </button>
            ) : (
              <span />
            )}
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => close(null)}>
                Cancel
              </Button>
              <Button type="submit" loading={busy} disabled={!value}>
                Confirm
              </Button>
            </div>
          </div>
        </form>
      </Dialog>
    </StepUpContext.Provider>
  );
}

export function useStepUp(): () => Promise<string | null> {
  const ask = useContext(StepUpContext);
  if (!ask) throw new Error("useStepUp needs <StepUpProvider>");
  return ask;
}

// --- Toasts --------------------------------------------------------------------------------

interface Toast {
  id: number;
  tone: "good" | "crit" | "info";
  text: string;
}

const ToastContext = createContext<((tone: Toast["tone"], text: string) => void) | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((tone: Toast["tone"], text: string) => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, tone, text }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 5000);
  }, []);
  const value = useMemo(() => push, [push]);
  return (
    <ToastContext.Provider value={value}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex flex-col items-center gap-2 px-4">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "pointer-events-auto rounded-[10px] px-4 py-3 text-sm font-medium shadow-lg",
              t.tone === "good" && "bg-good text-white",
              t.tone === "crit" && "bg-crit text-white",
              t.tone === "info" && "bg-brand text-on-brand",
            )}
          >
            {t.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): (tone: Toast["tone"], text: string) => void {
  const push = useContext(ToastContext);
  if (!push) throw new Error("useToast needs <ToastProvider>");
  return push;
}
