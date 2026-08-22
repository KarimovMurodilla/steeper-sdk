import type { LucideIcon } from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { formatCompact } from "@/lib/utils";

interface Props {
  label: string;
  value: number;
  icon: LucideIcon;
  color: string;
  hint?: string;
}

export function StatCard({ label, value, icon: Icon, color, hint }: Props) {
  return (
    <GlassCard className="p-4">
      <div className="flex items-center gap-3">
        <div
          className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-white/5 ${color}`}
        >
          <Icon size={20} />
        </div>
        <div className="min-w-0">
          <p
            className="text-2xl font-bold leading-tight text-tg-text"
            title={value.toLocaleString()}
          >
            {formatCompact(value)}
          </p>
          <p className="truncate text-xs text-tg-text-muted">{hint ?? label}</p>
        </div>
      </div>
    </GlassCard>
  );
}
