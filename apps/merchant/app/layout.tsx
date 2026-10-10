import type { Metadata, Viewport } from "next";

import { Providers } from "@/Providers";

import "@diyneco/shared-ui/fonts.css";
import "./globals.css";


export const metadata: Metadata = {
  title: { default: "Diyneco", template: "%s · Diyneco" },
  description: "Hotel operations: orders, rooms, billing and reports.",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = { themeColor: "#0b2350", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-ZA">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
