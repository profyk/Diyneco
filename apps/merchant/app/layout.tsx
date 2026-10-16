import type { Metadata, Viewport } from "next";

import { THEME_SCRIPT } from "@diyneco/shared-ui/theme-script";

import { Providers } from "@/Providers";

import "@diyneco/shared-ui/fonts.css";
import "./globals.css";


export const metadata: Metadata = {
  title: { default: "Diyneco", template: "%s · Diyneco" },
  description: "Hotel operations: orders, rooms, billing and reports.",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#0b2350" },
    { media: "(prefers-color-scheme: dark)", color: "#050d1c" },
  ],
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    // The saved light or dark choice is applied before the first paint (THEME_SCRIPT), so the
    // server's html and the browser's can differ in data-theme.
    <html lang="en-ZA" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
