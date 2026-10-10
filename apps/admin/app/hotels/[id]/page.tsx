import { HotelDetail } from "@/HotelDetail";

export const metadata = { title: "Hotel" };

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <HotelDetail id={id} />;
}
