import type { Metadata, Viewport } from "next";

import { MERCHANT_URL, settings } from "@/api";
import { DEFAULT_NAV } from "@/defaults";
import { PageView } from "@/PageView";
import { SiteHeader } from "@/SiteHeader";

import "@diyneco/shared-ui/fonts.css";
import "./globals.css";

export const revalidate = 300;

export async function generateMetadata(): Promise<Metadata> {
  const s = await settings();
  const seo = s.seo as { title_template?: string; default_title?: string; default_description?: string };
  const verification = s.verification as { google?: string; bing?: string };
  return {
    metadataBase: new URL(s.base_url),
    title: { default: seo.default_title ?? s.site_name, template: seo.title_template ?? `%s | ${s.site_name}` },
    description: seo.default_description,
    verification: {
      google: verification.google || undefined,
      other: verification.bing ? { "msvalidate.01": verification.bing } : undefined,
    },
    icons: { icon: "/brand/diyneco-logo.png" },
  };
}

export const viewport: Viewport = { themeColor: "#0b2350", width: "device-width", initialScale: 1 };

type Link = { label: string; href: string };

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const s = await settings();
  const nav = (s.navigation as Link[]).length ? (s.navigation as Link[]) : DEFAULT_NAV;
  const footer = s.footer as { columns?: { heading: string; links: Link[] }[]; note?: string };
  const contact = s.contact as { email?: string; phone?: string; address?: string };
  const social = s.social as { network: string; url: string }[];
  const columns = footer.columns?.length
    ? footer.columns
    : [
        { heading: "Product", links: [{ label: "Features", href: "/" }, { label: "Pricing", href: "/pricing" }, { label: "Book a demo", href: "/demo" }] },
        { heading: "Company", links: [{ label: "Blog", href: "/blog" }, { label: "Contact", href: "/contact" }] },
      ];
  return (
    <html lang={s.default_locale}>
      <body className="flex min-h-dvh flex-col">
        <SiteHeader siteName={s.site_name} links={nav} merchantUrl={MERCHANT_URL} />
        <main className="flex-1">{children}</main>
        <footer className="border-t border-line bg-surface">
          <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:px-6 md:grid-cols-4">
            <div>
              <p className="font-display text-lg font-semibold text-brand">{s.site_name}</p>
              {footer.note ? <p className="mt-2 text-sm text-muted">{footer.note}</p> : null}
              <div className="mt-3 flex flex-col gap-1 text-sm text-muted">
                {contact.email ? <a href={`mailto:${contact.email}`} className="hover:text-blue">{contact.email}</a> : null}
                {contact.phone ? <a href={`tel:${contact.phone.replace(/\s/g, "")}`} className="hover:text-blue">{contact.phone}</a> : null}
                {contact.address ? <span>{contact.address}</span> : null}
              </div>
            </div>
            {columns.map((c) => (
              <div key={c.heading}>
                <p className="text-sm font-semibold text-ink">{c.heading}</p>
                <ul className="mt-3 flex flex-col gap-2 text-sm">
                  {c.links.map((l) => (
                    <li key={l.href}>
                      <a href={l.href} className="text-muted hover:text-blue">
                        {l.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            <div>
              <p className="text-sm font-semibold text-ink">Legal</p>
              <ul className="mt-3 flex flex-col gap-2 text-sm">
                <li><a href="/legal/terms" className="text-muted hover:text-blue">Terms of service</a></li>
                <li><a href="/legal/privacy" className="text-muted hover:text-blue">Privacy notice</a></li>
                <li><a href="/legal" className="text-muted hover:text-blue">All legal documents</a></li>
              </ul>
              {social.length ? (
                <ul className="mt-4 flex flex-wrap gap-3 text-sm">
                  {social.map((x) => (
                    <li key={x.url}>
                      <a href={x.url} rel="noopener noreferrer" className="capitalize text-muted hover:text-blue">
                        {x.network === "x" ? "X" : x.network}
                      </a>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          </div>
          <p className="border-t border-line py-4 text-center text-xs text-muted">
            © {new Date().getFullYear()} {s.site_name}. All rights reserved.
          </p>
        </footer>
        <PageView locale={s.default_locale} enabled={(s.analytics as { provider?: string }).provider === "builtin"} />
      </body>
    </html>
  );
}
