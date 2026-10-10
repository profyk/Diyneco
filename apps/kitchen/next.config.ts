import type { NextConfig } from "next";

import { securityHeaders } from "../../packages/config/security-headers.mjs";

const config: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  transpilePackages: ["@diyneco/api-client", "@diyneco/shared-ui"],
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders(),
      },
    ];
  },
};

export default config;
