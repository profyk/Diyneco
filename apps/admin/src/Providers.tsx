"use client";

import { ToastProvider } from "@diyneco/shared-ui";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";

import { SessionProvider } from "./session";
import { Gate } from "./Shell";

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: 1, staleTime: 10_000, refetchOnWindowFocus: true },
          mutations: { retry: 0 },
        },
      }),
  );
  return (
    <QueryClientProvider client={client}>
      <ToastProvider>
        <SessionProvider>
          <Gate>{children}</Gate>
        </SessionProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
