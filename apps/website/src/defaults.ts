/**
 * Built-in pages shown until the same address is published from Admin > Website. They describe
 * only what Diyneco really does: no invented figures, customers or quotes.
 */

type Block = { type: string; [k: string]: unknown };

const art = (name: string, alt: string) => ({ url: `/images/hotel/${name}.svg`, alt, width: 1200, height: 800 });

/**
 * Illustrations bundled with the site (public/images/hotel), used by the built-in pages under
 * ids that cannot clash with uploaded images. They are drawings, not photos of real hotels;
 * real photos are uploaded and published from Admin > Website.
 */
export const DEFAULT_MEDIA: Record<string, { url: string; alt: string; width: number; height: number }> = {
  "builtin-devices": art("devices", "A guest tablet, a kitchen display and a staff phone showing the same room-service order"),
  "builtin-rooms": art("rooms", "A guest room with a tablet on the bedside table"),
  "builtin-reception": art("reception", "A hotel reception desk"),
  "builtin-kitchen": art("kitchen", "A hotel kitchen with an order display on the wall"),
  "builtin-restaurant": art("restaurant", "A hotel restaurant set for dinner"),
  "builtin-outside": art("outside", "A hotel building on a sunny day"),
  "builtin-pool": art("pool", "A hotel pool with loungers"),
};

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
        image_id: "builtin-devices",
      },
      {
        type: "features",
        heading: "Everything your team uses, connected",
        intro: "One system behind every screen, so nothing gets lost between reception, the kitchen and the guest.",
        items: [
          { title: "Guest room tablets", body: "Menus, ordering, requests for towels or cleaning, and hotel information in every room. Each new guest starts fresh: checkout clears the tablet.", image_id: "builtin-rooms" },
          { title: "Kitchen display", body: "Orders arrive the moment they are placed, by station, with a sound, large touch targets and a high-visibility mode.", image_id: "builtin-kitchen" },
          { title: "Reception and room service", body: "Reception checks guests in and out; runners see what is ready, pick it up and confirm delivery from their phone.", image_id: "builtin-reception" },
          { title: "Bills that add up", body: "Orders post to the room's bill automatically. Payments, tips and invoices reconcile to the cent." },
          { title: "Roles and approvals", body: "Owners, managers and staff each see what they need. Sensitive actions need a PIN, and adjustments need a second person." },
          { title: "Reports and daily close", body: "Revenue, payments, occupancy and kitchen times, ready for the end of each day." },
        ],
      },
      {
        type: "gallery",
        heading: "Made for every part of your property",
        intro: "From the rooms to the kitchen, the restaurant and the pool, every team works from the same system.",
        show_filters: true,
        items: [
          { image_id: "builtin-rooms", caption: "Guest rooms: order and ask from the tablet", category: "rooms" },
          { image_id: "builtin-reception", caption: "Reception: check-in, bills and requests", category: "reception" },
          { image_id: "builtin-kitchen", caption: "Kitchen: orders on the display, by station", category: "kitchen" },
          { image_id: "builtin-restaurant", caption: "Restaurant: charge meals to the room", category: "restaurant" },
          { image_id: "builtin-pool", caption: "Poolside: room service where guests are", category: "pool" },
          { image_id: "builtin-outside", caption: "Hotels, lodges and guest houses", category: "outside" },
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
