import { ChevronRight, Pencil, Trash2 } from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { useDeleteFunnel } from "@/hooks/useFunnels";
import { cn, formatDuration } from "@/lib/utils";
import type { FunnelViewModel } from "@/types/api";

interface Props {
  botId: string;
  funnels: FunnelViewModel[];
  selectedId: string | null;
  onSelect: (funnel: FunnelViewModel) => void;
  onEdit: (funnel: FunnelViewModel) => void;
}

export function FunnelList({
  botId,
  funnels,
  selectedId,
  onSelect,
  onEdit,
}: Props) {
  const remove = useDeleteFunnel(botId);

  return (
    <div className="space-y-2">
      {funnels.map((funnel) => (
        <GlassCard
          key={funnel.id}
          onClick={() => onSelect(funnel)}
          className={cn(
            "p-4 transition-colors",
            funnel.id === selectedId && "border-tg-primary/40 bg-tg-primary/10",
          )}
        >
          <div className="flex items-center gap-3">
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium">{funnel.name}</p>
              <p className="mt-1 truncate text-xs text-tg-text-muted">
                {funnel.steps.join(" → ")}
              </p>
              <p className="mt-1 text-xs text-tg-text-muted">
                {funnel.steps.length} steps ·{" "}
                {formatDuration(funnel.window_seconds)} window
              </p>
            </div>

            <div className="flex shrink-0 items-center gap-0.5">
              <button
                title="Edit funnel"
                aria-label="Edit funnel"
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(funnel);
                }}
                className="rounded-lg p-1.5 text-tg-text-muted transition-colors hover:bg-tg-overlay/10 hover:text-tg-text"
              >
                <Pencil size={14} />
              </button>
              <button
                title="Delete funnel"
                aria-label="Delete funnel"
                onClick={(e) => {
                  e.stopPropagation();
                  if (
                    !window.confirm(
                      `Delete the funnel "${funnel.name}"? The events it was built from are kept.`,
                    )
                  ) {
                    return;
                  }
                  remove.mutate(funnel.id);
                }}
                className="rounded-lg p-1.5 text-tg-text-muted transition-colors hover:bg-tg-overlay/10 hover:text-tg-red"
              >
                <Trash2 size={14} />
              </button>
              <ChevronRight size={16} className="text-tg-text-muted" />
            </div>
          </div>
        </GlassCard>
      ))}
    </div>
  );
}
