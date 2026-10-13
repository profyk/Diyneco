import { chooseApiUrl } from "@diyneco/api-client";

// The API address. NEXT_PUBLIC_API_FALLBACK_URL, when set, is used if the primary address does
// not answer when the app starts (D81); the app renders inside <ApiGate> until it is chosen.
const PRIMARY = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const FALLBACK = process.env.NEXT_PUBLIC_API_FALLBACK_URL ?? "";
export let API_URL = PRIMARY;
export const API_CHOICE_NEEDED = FALLBACK !== "" && FALLBACK !== PRIMARY;
export const apiReady: Promise<string> = chooseApiUrl([PRIMARY, FALLBACK]).then((url) => (API_URL = url));
export const apiUrl = (): string => API_URL;
