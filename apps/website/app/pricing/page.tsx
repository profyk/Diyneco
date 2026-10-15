import type { Metadata } from "next";

import { MERCHANT_URL, plans } from "@/api";
import { Blocks } from "@/blocks";
import { PricingTable } from "@/Pricing";

// Always the published plans from Admin > Plans & Pricing (GET /plans); never typed in here.

export const revalidate = 300;

export const metadata: Metadata = {
  title: "Pricing",
  description: "Plans for hotels, lodges and guest houses of every size. Start with a free trial.",
  alternates: { canonical: "/pricing" },
};

export default async function Page() {
  const data = await plans();
  return (
    <>
      <section className="bg-gradient-to-b from-tint to-bg">
        <div className="mx-auto max-w-6xl px-4 py-16 text-center sm:px-6">
          <h1 className="font-display text-4xl font-semibold tracking-tight text-ink sm:text-5xl">Simple pricing for every property</h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-muted">
            Choose by the size of your property. Every plan includes guest tablets, the kitchen display, room service and billing.
          </p>
        </div>
      </section>
      <section className="mx-auto max-w-6xl px-4 pb-16 sm:px-6">
        <PricingTable plans={data} signupUrl={`${MERCHANT_URL}/signup`} />
      </section>
      <Blocks
        blocks={[
          {
            type: "faq",
            heading: "Pricing questions",
            items: [
              { question: "Is there a free trial?", answer: "Yes. Nothing is charged during the trial; you choose a plan when you are ready." },
              { question: "Can I change plans later?", answer: "Yes, from Settings › Plan in the Merchant app. Changes follow your plan's upgrade and downgrade rules." },
              { question: "How do I pay?", answer: "Each period you receive an invoice; pay it online or by EFT, as offered for your country." },
              { question: "Do you have plans for groups?", answer: "One account can own several properties, each on its own plan. [Contact us](/contact) about larger groups." },
            ],
          },
        ]}
        ctx={{ media: {}, locale: "en", posts: [], countries: [] }}
      />
    </>
  );
}
