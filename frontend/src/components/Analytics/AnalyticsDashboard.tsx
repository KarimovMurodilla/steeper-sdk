import { useMemo, useState } from "react";
import {
  Users,
  MessageSquare,
  MessagesSquare,
  Activity,
  Radio,
  Zap,
  BarChart3,
} from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useBotAnalytics, useBotUpdateStats } from "@/hooks/useAnalytics";
import { cn, formatCompact } from "@/lib/utils";
import type { TimeGranularity } from "@/types/api";
import { StatCard } from "./StatCard";
import { AreaChart } from "./charts/AreaChart";
import { DonutChart } from "./charts/DonutChart";
import { BarList } from "./charts/BarList";

interface Props {
  botId: string | null;
}

const RANGES: {
  key: string;
  label: string;
  days: number;
  granularity: TimeGranularity;
}[] = [
  { key: "24h", label: "24h", days: 1, granularity: "hour" },
  { key: "7d", label: "7 days", days: 7, granularity: "day" },
  { key: "30d", label: "30 days", days: 30, granularity: "day" },
  { key: "90d", label: "90 days", days: 90, granularity: "week" },
];

export function AnalyticsDashboard({ botId }: Props) {
  const [rangeKey, setRangeKey] = useState("7d");
  const range = RANGES.find((r) => r.key === rangeKey) ?? RANGES[1]!;

  const since = useMemo(
    () => new Date(Date.now() - range.days * 86_400_000).toISOString(),
    [range.days],
  );

  const { data: summary, isLoading: summaryLoading } = useBotAnalytics(botId);
  const { data: stats, isLoading: statsLoading } = useBotUpdateStats(botId, {
    granularity: range.granularity,
    since,
  });

  if (!botId) {
    return (
      <EmptyState
        icon={BarChart3}
        title="No bot selected"
        description="Pick a bot above to explore its analytics."
        className="py-24"
      />
    );
  }

  if (summaryLoading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* All-time overview */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <StatCard
          label="Users"
          hint="Total users"
          value={summary?.users ?? 0}
          icon={Users}
          color="text-tg-accent"
        />
        <StatCard
          label="Chats"
          hint="Conversations"
          value={summary?.chats ?? 0}
          icon={MessageSquare}
          color="text-tg-green"
        />
        <StatCard
          label="Messages"
          hint="Total messages"
          value={summary?.messages ?? 0}
          icon={MessagesSquare}
          color="text-tg-orange"
        />
        <StatCard
          label="DAU"
          hint="Active today"
          value={summary?.dau ?? 0}
          icon={Activity}
          color="text-violet-400"
        />
      </div>

      {/* Telegram activity (windowed) */}
      <GlassCard className="p-5">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-semibold text-tg-text">Update volume</h3>
            <p className="text-xs text-tg-text-muted">
              Telegram updates received over time
            </p>
          </div>
          <div className="flex rounded-lg border border-white/10 bg-white/5 p-0.5">
            {RANGES.map((r) => (
              <button
                key={r.key}
                onClick={() => setRangeKey(r.key)}
                className={cn(
                  "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                  r.key === rangeKey
                    ? "bg-tg-primary text-white"
                    : "text-tg-text-secondary hover:text-tg-text",
                )}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-4 flex gap-8">
          <div>
            <p className="text-2xl font-bold text-tg-text">
              {formatCompact(stats?.total ?? 0)}
            </p>
            <p className="flex items-center gap-1 text-xs text-tg-text-muted">
              <Zap size={12} /> Updates
            </p>
          </div>
          <div>
            <p className="text-2xl font-bold text-tg-text">
              {formatCompact(stats?.active_users ?? 0)}
            </p>
            <p className="flex items-center gap-1 text-xs text-tg-text-muted">
              <Radio size={12} /> Active users
            </p>
          </div>
        </div>

        {statsLoading ? (
          <div className="flex h-60 items-center justify-center">
            <Spinner />
          </div>
        ) : stats && stats.timeseries.length > 0 ? (
          <AreaChart data={stats.timeseries} granularity={range.granularity} />
        ) : (
          <div className="flex h-60 items-center justify-center text-sm text-tg-text-muted">
            No activity in this period
          </div>
        )}
      </GlassCard>

      {/* Breakdowns */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GlassCard className="p-5">
          <h3 className="mb-4 font-semibold text-tg-text">Content types</h3>
          {statsLoading ? (
            <div className="flex h-40 items-center justify-center">
              <Spinner />
            </div>
          ) : stats && stats.by_content_type.length > 0 ? (
            <DonutChart data={stats.by_content_type} />
          ) : (
            <p className="py-10 text-center text-sm text-tg-text-muted">
              No message content in this period
            </p>
          )}
        </GlassCard>

        <GlassCard className="p-5">
          <h3 className="mb-4 font-semibold text-tg-text">Update types</h3>
          {statsLoading ? (
            <div className="flex h-40 items-center justify-center">
              <Spinner />
            </div>
          ) : stats && stats.by_type.length > 0 ? (
            <BarList data={stats.by_type} />
          ) : (
            <p className="py-10 text-center text-sm text-tg-text-muted">
              No updates in this period
            </p>
          )}
        </GlassCard>
      </div>
    </div>
  );
}
