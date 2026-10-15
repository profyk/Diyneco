/**
 * Built-in pages shown until the same address is published from Admin > Website. They describe
 * only what Diyneco really does: no invented figures, customers or quotes.
 */

type Block = { type: string; [k: string]: unknown };

export const DEFAULT_PAGES: Record<string, { title: string; description: string; blocks: Block[] }> = {
  "": {
    title: "Hotel operations in one place",
    description:
      "Guest tablets, kitchen displays, room service, billing and reports for hotels, lodges and guest houses.",
    blocks: [
      {
        type: "hero",
        eyebrow: "For hotels, lodges and guest houses",
        heading: "Run every order, room and bill from one place",
        subheading:
          "Guests order from the tablet in their room. The kitchen sees it at once, room service delivers it, and it lands on the guest's bill without anyone re-typing a thing.",
        primary: { label: "Start free trial", href: "/signup" },
        secondary: { label: "Book a demo", href: "/demo" },
      },
      {
        type: "features",
        heading: "Everything your team uses, connected",
        intro: "One system behind every screen, so nothing gets lost between reception, the kitchen and the guest.",
        items: [
          { title: "Guest room tablets", body: "Menus, ordering and hotel information in every room. Each new guest starts fresh: checkout clears the tablet." },
          { title: "Kitchen display", body: "Orders arrive the moment they are placed, by station, with large touch targets and a high-visibility mode." },
          { title: "Room service", body: "Runners see what is ready, pick it up and confirm delivery from their phone." },
          { title: "Bills that add up", body: "Orders post to the room's bill automatically. Payments, tips and invoices reconcile to the cent." },
          { title: "Roles and approvals", body: "Owners, managers and staff each see what they need. Sensitive actions need a PIN, and adjustments need a second person." },
          { title: "Reports and daily close", body: "Revenue, payments, occupancy and kitchen times, ready for the end of each day." },
        ],
      },
      {
        type: "steps",
        heading: "Up and running in a day",
        items: [
          { title: "Register your property", body: "Choose your country; currency, time zone and tax defaults follow." },
          { title: "Add rooms and your menu", body: "Room types, rooms, menu categories and items with prices." },
          { title: "Set up the tablets", body: "Pair each room tablet and kitchen display with a code from the Merchant app." },
          { title: "Take your first order", body: "Guests order, the kitchen prepares, room service delivers, the bill updates." },
        ],
      },
      { type: "pricing", heading: "Simple pricing", intro: "Pick a plan by the size of your property. Start with a free trial." },
      {
        type: "faq",
        heading: "Questions",
        items: [
          { question: "Is there a free trial?", answer: "Yes. Nothing is charged during the trial, and you choose a plan when you are ready." },
          { question: "Which tablets do I need?", answer: "Android tablets for guest rooms and the kitchen display. Staff can use the web apps on any modern browser." },
          { question: "Which currencies and countries do you support?", answer: "Prices and bills use your country's currency, with its tax name and rate as a starting point. Registration opens country by country." },
          { question: "Who can see guest information?", answer: "Only your own staff, according to their role. Diyneco staff see account totals, never guest records." },
        ],
      },
      {
        type: "cta",
        heading: "See it working in your property",
        body: "Start a free trial, or let us walk you through it.",
        primary: { label: "Start free trial", href: "/signup" },
        secondary: { label: "Book a demo", href: "/demo" },
      },
    ],
  },
  contact: {
    title: "Contact us",
    description: "Questions about Diyneco? Send us a message.",
    blocks: [{ type: "lead_form", kind: "contact", heading: "Contact us", intro: "We usually reply within one working day." }],
  },
  demo: {
    title: "Book a demo",
    description: "See Diyneco in action for your hotel, lodge or guest house.",
    blocks: [
      {
        type: "lead_form",
        kind: "demo",
        heading: "Book a demo",
        intro: "Tell us about your property and we will show you how Diyneco would work there.",
      },
    ],
  },
};

export const DEFAULT_NAV = [
  { label: "Product", href: "/" },
  { label: "Pricing", href: "/pricing" },
  { label: "Blog", href: "/blog" },
  { label: "Contact", href: "/contact" },
];
