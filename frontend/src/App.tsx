import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { AppLayout } from "@/components/Layout/AppLayout";
import { LoginPage } from "@/pages/LoginPage";
import { Spinner } from "@/components/ui/Spinner";

// Routes are split out of the entry bundle: charts, the log viewer and the
// funnel editor are dead weight for a user who only opens the login screen.
const ChatPage = lazy(() =>
  import("@/pages/ChatPage").then((m) => ({ default: m.ChatPage })),
);
const BroadcastsPage = lazy(() =>
  import("@/pages/BroadcastsPage").then((m) => ({ default: m.BroadcastsPage })),
);
const MetricsPage = lazy(() =>
  import("@/pages/MetricsPage").then((m) => ({ default: m.MetricsPage })),
);
const FunnelsPage = lazy(() =>
  import("@/pages/FunnelsPage").then((m) => ({ default: m.FunnelsPage })),
);
const LogsPage = lazy(() =>
  import("@/pages/LogsPage").then((m) => ({ default: m.LogsPage })),
);
const NotFoundPage = lazy(() =>
  import("@/pages/NotFoundPage").then((m) => ({ default: m.NotFoundPage })),
);

function RouteFallback() {
  return (
    <div className="flex h-full min-h-[60vh] items-center justify-center">
      <Spinner size="lg" />
    </div>
  );
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<RouteFallback />}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<AppLayout />}>
              <Route path="/" element={<Navigate to="/chats" replace />} />
              <Route path="/chats" element={<ChatPage />} />
              <Route path="/broadcasts" element={<BroadcastsPage />} />
              <Route path="/metrics" element={<MetricsPage />} />
              <Route path="/funnels" element={<FunnelsPage />} />
              <Route path="/logs" element={<LogsPage />} />
            </Route>
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 6000,
          error: { duration: 8000 },
          style: {
            background: "rgb(var(--tg-surface))",
            color: "rgb(var(--tg-text))",
            border: "1px solid rgb(var(--tg-overlay) / 0.1)",
            borderRadius: "12px",
          },
        }}
      />
    </QueryClientProvider>
  );
}
