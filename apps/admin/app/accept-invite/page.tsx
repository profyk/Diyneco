import { Suspense } from "react";

import { AcceptInvite } from "@/AcceptInvite";

export const metadata = { title: "Join", referrer: "no-referrer" };

export default function Page() {
  return (
    <Suspense>
      <AcceptInvite />
    </Suspense>
  );
}
