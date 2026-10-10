// Security headers shared by every Diyneco web app (security spec: browser hardening).
//
// The Content-Security-Policy lets a page talk only to itself, the Diyneco API (HTTP and
// WebSocket) and file storage. Next.js renders inline bootstrap scripts, so script-src keeps
// 'unsafe-inline' (no third-party origins are allowed, which is what blocks injected loaders);
// development adds 'unsafe-eval' for React's dev tooling.
//
// NEXT_PUBLIC_API_URL      the API origin (default http://localhost:8000)
// NEXT_PUBLIC_STORAGE_URL  where signed uploads and downloads go; defaults to Supabase
//                          projects (https://*.supabase.co). Local storage is served by the API.

/** @param {string} url */
function origin(url) {
  try {
    return new URL(url).origin;
  } catch {
    return "";
  }
}

/**
 * @param {{ dev?: boolean }} [options]
 * @returns {{ key: string, value: string }[]}
 */
export function securityHeaders({ dev = process.env.NODE_ENV !== "production" } = {}) {
  const api = origin(process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");
  const ws = api.replace(/^http/, "ws");
  const storage = process.env.NEXT_PUBLIC_STORAGE_URL ? origin(process.env.NEXT_PUBLIC_STORAGE_URL) : "https://*.supabase.co";
  const csp = [
    "default-src 'self'",
    `script-src 'self' 'unsafe-inline'${dev ? " 'unsafe-eval'" : ""}`,
    "style-src 'self' 'unsafe-inline'",
    `img-src 'self' data: blob: ${api} ${storage}`,
    "font-src 'self'",
    `connect-src 'self' ${api} ${ws} ${storage}${dev ? " ws://localhost:*" : ""}`,
    "manifest-src 'self'",
    "worker-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    ...(dev ? [] : ["upgrade-insecure-requests"]),
  ].join("; ");
  return [
    { key: "Content-Security-Policy", value: csp },
    { key: "X-Frame-Options", value: "DENY" },
    { key: "X-Content-Type-Options", value: "nosniff" },
    { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
    { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=(), usb=()" },
    { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
    ...(dev ? [] : [{ key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" }]),
  ];
}
