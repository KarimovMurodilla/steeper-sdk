import { Outlet, Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useMe } from "@/hooks/useAuth";
import { Sidebar } from "./Sidebar";
import { MobileTopBar } from "./MobileTopBar";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { CommandPalette } from "@/components/CommandPalette";
import { Spinner } from "@/components/ui/Spinner";

export function AppLayout() {
  const { isAuthenticated } = useAuthStore();
  const { isLoading } = useMe();
  const location = useLocation();

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-tg-bg bg-[radial-gradient(120%_120%_at_100%_0%,rgb(var(--tg-primary)/0.10),transparent_55%)]">
      <Sidebar />
      <CommandPalette />
      <div className="flex min-w-0 flex-1 flex-col">
        <MobileTopBar />
        <main className="min-h-0 flex-1 overflow-auto">
          <ErrorBoundary resetKey={location.pathname}>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
