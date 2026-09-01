import { TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./Button";

interface Props {
  title?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Something went wrong",
  description = "The request did not go through. Check your connection and try again.",
  onRetry,
  className,
}: Props) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center justify-center py-16 text-center",
        className,
      )}
    >
      <TriangleAlert
        size={48}
        className="mb-4 text-tg-red/80"
        strokeWidth={1.5}
      />
      <h3 className="text-lg font-medium text-tg-text-secondary">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-tg-text-muted">{description}</p>
      {onRetry && (
        <Button variant="secondary" className="mt-4" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
