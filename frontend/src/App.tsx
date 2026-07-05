import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { AppLayout } from "@/components/Layout/AppLayout";
import { LoginPage } from "@/pages/LoginPage";
import { ChatPage } from "@/pages/ChatPage";
import { BroadcastsPage } from "@/pages/BroadcastsPage";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

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
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/chats" replace />} />
            <Route path="/chats" element={<ChatPage />} />
            <Route path="/broadcasts" element={<BroadcastsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#182533",
            color: "#f5f5f5",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: "12px",
          },
        }}
      />
    </QueryClientProvider>
  );
}
