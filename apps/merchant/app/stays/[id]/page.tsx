import { StayDetail } from "@/screens/StayDetail";

export const metadata = { title: "Stay" };

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <StayDetail id={id} />;
}
