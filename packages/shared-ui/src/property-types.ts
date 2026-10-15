/** Property categories (D84, D85). Must match PropertyType in backend/app/schemas/hotel.py. */
export const PROPERTY_TYPES = [
  { value: "hotel", label: "Hotel", group: "Hotels and resorts" },
  { value: "boutique_hotel", label: "Boutique hotel", group: "Hotels and resorts" },
  { value: "resort", label: "Resort", group: "Hotels and resorts" },
  { value: "motel", label: "Motel", group: "Hotels and resorts" },
  { value: "inn", label: "Inn", group: "Hotels and resorts" },
  { value: "lodge", label: "Lodge (safari, game or country)", group: "Lodges and guest houses" },
  { value: "guest_house", label: "Guest house", group: "Lodges and guest houses" },
  { value: "bed_and_breakfast", label: "Bed and breakfast", group: "Lodges and guest houses" },
  { value: "country_house", label: "Country house", group: "Lodges and guest houses" },
  { value: "aparthotel", label: "Aparthotel", group: "Apartments and homes" },
  { value: "serviced_apartments", label: "Serviced apartments", group: "Apartments and homes" },
  { value: "holiday_home", label: "Holiday home or villa", group: "Apartments and homes" },
  { value: "hostel", label: "Hostel", group: "Budget and outdoors" },
  { value: "camp", label: "Camp or glamping", group: "Budget and outdoors" },
  { value: "other", label: "Other", group: "Other" },
] as const;

export type PropertyType = (typeof PROPERTY_TYPES)[number]["value"];

export function propertyTypeLabel(value: string | null | undefined): string {
  return PROPERTY_TYPES.find((t) => t.value === value)?.label ?? "Not set";
}

/** The categories in their groups, in display order, for <optgroup> lists. */
export function propertyTypeGroups(): { group: string; items: { value: string; label: string }[] }[] {
  const out: { group: string; items: { value: string; label: string }[] }[] = [];
  for (const t of PROPERTY_TYPES) {
    let g = out.find((x) => x.group === t.group);
    if (!g) out.push((g = { group: t.group, items: [] }));
    g.items.push({ value: t.value, label: t.label });
  }
  return out;
}
