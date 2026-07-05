import { Outlet, Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useMe } from "@/hooks/useAuth";
import { Sidebar } from "./Sidebar";
import { Spinner } from "@/components/ui/Spinner";

export function AppLayout() {
  const { isAuthenticated } = useAuthStore();
  const { isLoading } = useMe();

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
    <div className="flex h-screen overflow-hidden bg-tg-bg bg-[radial-gradient(120%_120%_at_100%_0%,rgba(82,136,193,0.10),transparent_55%)]">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
