"use client";

/**
 * Staff session for the web: the access token lives only in memory; the refresh token is an
 * httpOnly cookie the API sets for allowed web origins, so a page reload restores the
 * session with POST /auth/refresh and nothing secret ever touches local storage.
 */
import { type Api, ApiError, type components, createApi, type ErrorBody, ok } from "@diyneco/api-client";
import { StepUpProvider, useStepUp } from "@diyneco/shared-ui";
import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { API_URL } from "./config";

type Me = components["schemas"]["MeOut"];
type TokenResponse = components["schemas"]["TokenResponse"];
export type Membership = components["schemas"]["HotelMembershipOut"];

export type SessionState =
  | { status: "loading" }
  | { status: "signed-out" }
  | { status: "mfa-enrol" }
  | { status: "signed-in"; me: Me; hotels: Membership[] };

interface SessionContext {
  state: SessionState;
  api: Api;
  can: (permission: string) => boolean;
  /** The current access token (refreshed if missing), for the realtime connection. */
  accessToken: () => Promise<string | null>;
  signIn: (email: string, password: string) => Promise<{ mfaToken: string } | null>;
  verifyMfa: (mfaToken: string, code: string, recovery?: boolean) => Promise<void>;
  completeEnrolment: (tokens: TokenResponse) => Promise<void>;
  switchHotel: (hotelId: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const Ctx = createContext<SessionContext | null>(null);

async function post<T>(path: string, body: unknown): Promise<{ status: number; data: T }> {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  const data = res.status === 204 ? ({} as T) : await res.json();
  if (!res.ok) throw new ApiError(res.status, (data as { error: ErrorBody }).error);
  return { status: res.status, data: data as T };
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const token = useRef<string | null>(null);
  const [state, setState] = useState<SessionState>({ status: "loading" });
  const stepUpRef = useRef<() => Promise<string | null>>(async () => null);

  const refresh = useCallback(async (hotelId?: string): Promise<string | null> => {
    try {
      const { data } = await post<TokenResponse>("/auth/refresh", hotelId ? { hotel_id: hotelId } : {});
      token.current = data.access_token;
      return data.access_token;
    } catch {
      token.current = null;
      return null;
    }
  }, []);

  const api = useMemo(
    () =>
      createApi({
        baseUrl: API_URL,
        credentials: "include",
        getToken: () => token.current,
        refresh: () => refresh(),
        onSignedOut: () => setState({ status: "signed-out" }),
        stepUp: () => stepUpRef.current(),
      }),
    [refresh],
  );

  const load = useCallback(
    async (hotels?: Membership[]) => {
      const me = await ok(api.GET("/api/v1/auth/me"));
      if (me.mfa_pending) {
        setState({ status: "mfa-enrol" });
        return;
      }
      setState({ status: "signed-in", me, hotels: hotels ?? [] });
    },
    [api],
  );

  const accept = useCallback(
    async (tokens: TokenResponse) => {
      token.current = tokens.access_token;
      if (tokens.mfa_enrolment_required) {
        setState({ status: "mfa-enrol" });
        return;
      }
      await load(tokens.hotels);
    },
    [load],
  );

  useEffect(() => {
    (async () => {
      try {
        const { data } = await post<TokenResponse>("/auth/refresh", {});
        await accept(data);
      } catch {
        setState({ status: "signed-out" });
      }
    })();
  }, [accept]);

  const value = useMemo<SessionContext>(
    () => ({
      state,
      api,
      can: (permission) => state.status === "signed-in" && state.me.permissions.includes(permission),
      accessToken: async () => token.current ?? (await refresh()),
      async signIn(email, password) {
        const { data } = await post<TokenResponse | { mfa_required: true; mfa_token: string }>("/auth/login", {
          email,
          password,
        });
        if ("mfa_token" in data) return { mfaToken: data.mfa_token };
        await accept(data);
        return null;
      },
      async verifyMfa(mfaToken, code, recovery = false) {
        const { data } = await post<TokenResponse>(
          "/auth/mfa/verify",
          recovery ? { mfa_token: mfaToken, recovery_code: code } : { mfa_token: mfaToken, code },
        );
        await accept(data);
      },
      completeEnrolment: accept,
      async switchHotel(hotelId) {
        const { data } = await post<TokenResponse>("/auth/refresh", { hotel_id: hotelId });
        await accept(data);
      },
      async signOut() {
        await api.POST("/api/v1/auth/logout").catch(() => undefined);
        token.current = null;
        setState({ status: "signed-out" });
      },
    }),
    [state, api, accept, refresh],
  );

  // The PIN dialog exchanges a PIN or password for a step-up token (POST /auth/step-up).
  return (
    <StepUpProvider
      request={async (secret) => (await ok(api.POST("/api/v1/auth/step-up", { body: secret }))).step_up_token}
    >
      <Register target={stepUpRef} />
      <Ctx.Provider value={value}>{children}</Ctx.Provider>
    </StepUpProvider>
  );
}

function Register({ target }: { target: { current: () => Promise<string | null> } }) {
  const ask = useStepUp();
  useEffect(() => {
    target.current = ask;
  }, [ask, target]);
  return null;
}

export function useSession(): SessionContext {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useSession needs <SessionProvider>");
  return ctx;
}

/** The hotel's own currency (chosen by the hotel; never assumed). */
export function useCurrency(): string {
  const { state } = useSession();
  if (state.status !== "signed-in" || !state.me.hotel) throw new Error("no hotel");
  return state.me.hotel.currency;
}

/** The signed-in state; only use inside the authenticated shell. */
export function useMe() {
  const { state } = useSession();
  if (state.status !== "signed-in") throw new Error("not signed in");
  return state;
}
