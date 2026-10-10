import { Suspense } from "react";

import { Guests } from "@/screens/Lists";

export const metadata = { title: "Guests" };

export default function Page() {
  return (
    <Suspense>
      <Guests />
    </Suspense>
  );
}
