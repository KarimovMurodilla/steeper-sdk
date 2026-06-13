import { useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useLogin } from "@/hooks/useAuth";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

export function LoginPage() {
  const { isAuthenticated } = useAuthStore();
  const loginMutation = useLogin();

  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");

  if (isAuthenticated()) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loginMutation.mutate({ login, password });
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-tg-bg px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-tg-primary text-2xl font-bold text-white shadow-lg shadow-tg-primary/30">
            S
          </div>
          <h1 className="text-2xl font-bold">Welcome to Steeper</h1>
          <p className="mt-1 text-sm text-tg-text-secondary">
            Sign in to manage your Telegram bots
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-[20px] p-6 shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Login"
              placeholder="Enter your login"
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              autoComplete="username"
              autoFocus
            />
            <Input
              label="Password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
            <Button
              type="submit"
              loading={loginMutation.isPending}
              className="w-full"
              size="lg"
            >
              Sign In
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
