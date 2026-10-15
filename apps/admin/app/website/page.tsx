import { Suspense } from "react";

import { Website } from "@/Website";

export const metadata = { title: "Website" };

export default function Page() {
  return (
    <Suspense>
      <Website />
    </Suspense>
  );
}
