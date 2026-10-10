"use client";

import { ToastProvider } from "@diyneco/shared-ui";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { App } from "./RoomService";
import { SessionProvider } from "./session";

export function Providers() {
  const [client] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 5_000 }, mutations: { retry: 0 } } }),
  );
  return (
    <QueryClientProvider client={client}>
      <ToastProvider>
        <SessionProvider>
          <App />
        </SessionProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
