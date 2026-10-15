import { WebsiteEditor } from "@/WebsiteEditor";

export const metadata = { title: "Edit page" };

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <WebsiteEditor id={id} />;
}
