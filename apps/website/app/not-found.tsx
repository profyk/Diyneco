export default function NotFound() {
  return (
    <section className="mx-auto flex max-w-xl flex-col items-center px-4 py-24 text-center">
      <p className="text-sm font-semibold uppercase tracking-wide text-blue">404</p>
      <h1 className="mt-2 font-display text-3xl font-semibold text-ink">This page isn&apos;t here</h1>
      <p className="mt-3 text-muted">It may have moved. Try the home page or get in touch.</p>
      <div className="mt-8 flex gap-3">
        <a href="/" className="inline-flex h-11 items-center rounded-[10px] bg-brand px-5 font-medium text-on-brand">
          Home
        </a>
        <a href="/contact" className="inline-flex h-11 items-center rounded-[10px] border border-line px-5 font-medium text-ink">
          Contact
        </a>
      </div>
    </section>
  );
}
