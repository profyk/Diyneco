import { Suspense } from "react";

import { Orders } from "@/screens/Orders";

export const metadata = { title: "Orders" };

export default function Page() {
  return (
    <Suspense>
      <Orders />
    </Suspense>
  );
}
