import { Suspense } from "react";

import { VerifyEmail } from "@/screens/Public";

export const metadata = { title: "Confirm email", referrer: "no-referrer" };

export default function Page() {
  return (
    <Suspense>
      <VerifyEmail />
    </Suspense>
  );
}
