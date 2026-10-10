/**
 * The tablet's identity. A room tablet is a dedicated, pinned kiosk browser, so its long-lived
 * device credential is kept in local storage (the only durable storage a browser offers); it
 * is exchanged for 1-hour device tokens kept in memory. Unpairing the tablet in the Merchant
 * app revokes the credential immediately. Nothing about a guest is ever stored here.
 */
import { API_URL, APP_VERSION } from "./config";

const CREDENTIAL_KEY = "diyneco.guest.credential";

function read(storage: Storage | undefined, key: string): string | null {
  try {
    return storage?.getItem(key) ?? null;
  } catch {
    return null;
  }
}

function write(storage: Storage | undefined, key: string, value: string | null): void {
  try {
    if (value === null) storage?.removeItem(key);
    else storage?.setItem(key, value);
  } catch {
    /* private mode: stays in memory only */
  }
}

const local = typeof window !== "undefined" ? window.localStorage : undefined;

let deviceToken: { token: string; expiresAt: number } | null = null;

export const credential = {
  get: () => read(local, CREDENTIAL_KEY),
  set: (value: string) => write(local, CREDENTIAL_KEY, value),
  clear: () => {
    write(local, CREDENTIAL_KEY, null);
    deviceToken = null;
  },
};

export class DeviceRevoked extends Error {}

/** A valid device token, exchanging the credential when the current one is about to expire. */
export async function getDeviceToken(force = false): Promise<string | null> {
  if (!force && deviceToken && deviceToken.expiresAt - Date.now() > 60_000) return deviceToken.token;
  const cred = credential.get();
  if (!cred) return null;
  const res = await fetch(`${API_URL}/api/v1/devices/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ device_credential: cred }),
  });
  if (res.status === 401) {
    credential.clear();
    throw new DeviceRevoked("This display was unpaired.");
  }
  if (!res.ok) return deviceToken?.token ?? null;
  const body = (await res.json()) as { access_token: string; expires_in: number };
  deviceToken = { token: body.access_token, expiresAt: Date.now() + body.expires_in * 1000 };
  return deviceToken.token;
}

export function currentDeviceToken(): string | null {
  return deviceToken?.token ?? null;
}

export const appVersion = APP_VERSION;
