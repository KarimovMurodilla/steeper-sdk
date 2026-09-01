import type { CSSProperties } from "react";
import { cn } from "@/lib/utils";

interface Props {
  className?: string;
  style?: CSSProperties;
}

/** Neutral placeholder block that mirrors the shape of the pending content. */
export function Skeleton({ className, style }: Props) {
  return (
    <div
      aria-hidden
      style={style}
      className={cn(
        "animate-pulse rounded-md bg-tg-overlay/5 motion-reduce:animate-none",
        className,
      )}
    />
  );
}

/** Rows of the chat list, matching avatar + two text lines. */
export function ChatListSkeleton({ rows = 8 }: { rows?: number }) {
  return (
    <div className="space-y-1 p-3" aria-busy="true" aria-label="Loading chats">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 py-1.5">
          <Skeleton className="h-10 w-10 flex-shrink-0 rounded-full" />
          <div className="min-w-0 flex-1 space-y-2">
            <Skeleton className="h-3.5 w-1/3" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Stacked cards, used by the broadcast and funnel lists. */
export function CardListSkeleton({
  rows = 4,
  className,
}: {
  rows?: number;
  className?: string;
}) {
  return (
    <div className={cn("space-y-3", className)} aria-busy="true">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="rounded-xl border border-tg-overlay/5 bg-tg-overlay/[0.02] p-4"
        >
          <div className="flex items-center gap-3">
            <div className="min-w-0 flex-1 space-y-2">
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-3 w-2/3" />
            </div>
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Placeholder that occupies the same box as a rendered chart. */
export function ChartSkeleton({ className }: Props) {
  return <Skeleton className={cn("h-60 w-full", className)} />;
}
