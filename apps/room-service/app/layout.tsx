import type { Metadata, Viewport } from "next";

import "@diyneco/shared-ui/fonts.css";
import "./globals.css";


export const metadata: Metadata = {
  title: "Room service · Diyneco",
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, title: "Room service", statusBarStyle: "default" },
  robots: { index: false, follow: false },
};

export const viewport: Viewport = { themeColor: "#0b2350", width: "device-width", initialScale: 1, viewportFit: "cover" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
