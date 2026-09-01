import { Link, useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, Home } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";

export function NotFoundPage() {
  useDocumentTitle("Page not found");
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-tg-bg px-4 text-center">
      <img src="/logo.png" alt="" className="mb-6 h-14 w-14 rounded-2xl" />
      <h1 className="mb-2 text-6xl font-bold text-tg-primary">404</h1>
      <p className="text-lg text-tg-text-secondary">Page not found</p>
      <p className="mt-1 max-w-sm break-all text-sm text-tg-text-muted">
        Nothing is routed at <code>{location.pathname}</code>.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <Button variant="secondary" onClick={() => navigate(-1)}>
          <ArrowLeft size={16} />
          Go back
        </Button>
        <Link to="/chats">
          <Button>
            <Home size={16} />
            Back to chats
          </Button>
        </Link>
      </div>
    </div>
  );
}
