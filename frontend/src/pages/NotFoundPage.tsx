import { Link } from "react-router-dom";
import { Home } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center text-center px-4">
      <h1 className="text-6xl font-bold text-tg-primary mb-2">404</h1>
      <p className="text-lg text-tg-text-secondary mb-6">Page not found</p>
      <Link to="/">
        <Button>
          <Home size={16} />
          Back to Home
        </Button>
      </Link>
    </div>
  );
}
