"use client";

import { ApiGate, ToastProvider } from "@diyneco/shared-ui";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";

import { API_CHOICE_NEEDED, apiReady } from "./config";
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
        <ApiGate ready={apiReady} needed={API_CHOICE_NEEDED}>
          <SessionProvider>
            <Gate>{children}</Gate>
          </SessionProvider>
        </ApiGate>
      </ToastProvider>
    </QueryClientProvider>
  );
}
