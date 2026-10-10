import { Suspense } from "react";

import { ResetPassword } from "@/screens/Public";

export const metadata = { title: "New password" };

export default function Page() {
  return (
    <Suspense>
      <ResetPassword />
    </Suspense>
  );
}
