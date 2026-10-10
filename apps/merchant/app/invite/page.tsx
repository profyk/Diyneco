import { Suspense } from "react";

import { AcceptInvite } from "@/screens/Public";

export const metadata = { title: "Join your hotel", referrer: "no-referrer" };

export default function Page() {
  return (
    <Suspense>
      <AcceptInvite />
    </Suspense>
  );
}
