import { timingSafeEqual } from "node:crypto";

import { revalidatePath } from "next/cache";

// Called by the API after a publish (D83) with the changed paths, so visitors see the change
// at once instead of within five minutes. Needs WEBSITE_REVALIDATE_SECRET on both sides.

function same(a: string, b: string): boolean {
  const x = Buffer.from(a);
  const y = Buffer.from(b);
  return x.length === y.length && timingSafeEqual(x, y);
}

export async function POST(request: Request): Promise<Response> {
  const secret = process.env.WEBSITE_REVALIDATE_SECRET ?? "";
  if (!secret || !same(request.headers.get("x-revalidate-secret") ?? "", secret)) {
    return Response.json({ ok: false }, { status: 401 });
  }
  const body = (await request.json().catch(() => ({}))) as { paths?: unknown; everything?: unknown };
  if (body.everything === true) {
    revalidatePath("/", "layout");
    return Response.json({ ok: true, everything: true });
  }
  const paths = Array.isArray(body.paths) ? body.paths.filter((p): p is string => typeof p === "string" && p.startsWith("/")).slice(0, 100) : [];
  for (const p of paths) revalidatePath(p);
  revalidatePath("/sitemap.xml");
  return Response.json({ ok: true, paths });
}
