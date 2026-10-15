import path from "node:path";

import type { NextConfig } from "next";

import { securityHeaders } from "../../packages/config/security-headers.mjs";

const config: NextConfig = {
  ...(process.env.NEXT_OUTPUT === "standalone"
    ? { output: "standalone" as const, outputFileTracingRoot: path.resolve(process.cwd(), "../..") }
    : {}),
  reactStrictMode: true,
  poweredByHeader: false,
  transpilePackages: ["@diyneco/api-client", "@diyneco/shared-ui"],
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders() }];
  },
};

export default config;
