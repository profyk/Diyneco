# Diyneco website (www.diyneco.com)

The public marketing site (DECISIONS D83, D88). Content comes from the API, so nothing is
edited here:

| What | Where it is managed | Address |
| --- | --- | --- |
| Pages and blog posts | Admin › Website (published entries) | `/`, `/<page>`, `/blog`, `/blog/<post>` |
| Pricing | Admin › Plans & Pricing (published plans and prices) | `/pricing` and any page's pricing block |
| Terms, privacy and other legal documents | Admin › Legal documents | `/legal`, `/legal/<kind>` |
| Countries in the contact form | Admin › Countries | contact and demo forms |
| Leads (demo and contact requests) | Admin › Website › Leads | `/contact`, `/demo` |

Until a page is published at an address, the site shows a built-in version of the home,
contact and demo pages. `/pricing` and `/legal` always read the admin data.

## Run locally

```
pnpm --filter @diyneco/website dev     # http://localhost:3006
```

## Deploy on Vercel

New project › import this repository › **Root Directory** `apps/website` (keep "Include
files outside the root directory" on). `vercel.json` sets the build. Environment variables:

| Variable | Value |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | the API, e.g. `https://api.diyneco.com` (or the Railway address) |
| `NEXT_PUBLIC_MERCHANT_URL` | the Merchant app, for Sign in and Start free trial |
| `WEBSITE_REVALIDATE_SECRET` | a long random value; set the same value as `WEBSITE_REVALIDATE_SECRET` on the API, and `WEBSITE_URL` on the API to this site's address, so publishing refreshes pages at once |
| `ENABLE_EXPERIMENTAL_COREPACK` | `1` |

Pages are cached for 5 minutes. Images are served by the API, which the Content-Security-Policy
allows through `NEXT_PUBLIC_API_URL`.
