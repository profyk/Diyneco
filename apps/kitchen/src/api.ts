import { createApi } from "@diyneco/api-client";

import { API_URL } from "./config";
import { cookSession, currentDeviceToken, getDeviceToken } from "./device";

/** Reads the board as the display (device token). */
export const deviceApi = createApi({
  baseUrl: API_URL,
  getToken: currentDeviceToken,
  refresh: () => getDeviceToken(true),
});

let onCookEnded: () => void = () => {};
export function whenCookSessionEnds(fn: () => void): void {
  onCookEnded = fn;
}

/** Acts as the signed-in cook (kitchen session from their PIN). */
export const cookApi = createApi({
  baseUrl: API_URL,
  getToken: () => cookSession.get()?.token ?? null,
  onSignedOut: () => {
    cookSession.clear();
    onCookEnded();
  },
  refresh: async () => null, // kitchen sessions do not refresh; the cook signs in again
});
