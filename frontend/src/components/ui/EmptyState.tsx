import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  icon: LucideIcon;
  title: string;
  description?: string;
  className?: string;
  action?: React.ReactNode;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  className,
  action,
}: Props) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-16 text-center",
        className,
      )}
    >
      <Icon size={48} className="text-tg-text-muted mb-4" strokeWidth={1.5} />
      <h3 className="text-lg font-medium text-tg-text-secondary">{title}</h3>
      {description && (
        <p className="mt-1 max-w-sm text-sm text-tg-text-muted">
          {description}
        </p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
