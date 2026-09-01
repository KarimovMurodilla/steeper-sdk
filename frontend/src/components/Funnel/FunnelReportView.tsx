import { useMemo, useState } from "react";
import { Filter, TrendingDown } from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { ChartSkeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { FunnelChart } from "./FunnelChart";
import { useFunnelReport } from "@/hooks/useFunnels";
import { cn, formatDuration, formatPercent } from "@/lib/utils";
import type { FunnelViewModel } from "@/types/api";

interface Props {
  botId: string;
  funnel: FunnelViewModel;
}

const RANGES = [
  { key: "7d", label: "7 days", days: 7 },
  { key: "30d", label: "30 days", days: 30 },
  { key: "90d", label: "90 days", days: 90 },
] as const;

type RangeKey = (typeof RANGES)[number]["key"];

export function FunnelReportView({ botId, funnel }: Props) {
  const [rangeKey, setRangeKey] = useState<RangeKey>("30d");
  const [matureOnly, setMatureOnly] = useState(false);

  const params = useMemo(() => {
    const days = RANGES.find((r) => r.key === rangeKey)!.days;
    return {
      since: new Date(Date.now() - days * 86_400_000).toISOString(),
      mature_only: matureOnly,
    };
  }, [rangeKey, matureOnly]);

  const { data, isLoading } = useFunnelReport(botId, funnel.id, params);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-1">
          {RANGES.map((range) => (
            <button
              key={range.key}
              onClick={() => setRangeKey(range.key)}
              className={cn(
                "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
                rangeKey === range.key
                  ? "bg-tg-primary/20 text-tg-accent"
                  : "text-tg-text-secondary hover:bg-tg-overlay/5",
              )}
            >
              {range.label}
            </button>
          ))}
        </div>

        <button
          onClick={() => setMatureOnly((v) => !v)}
          title={
            matureOnly
              ? "Only users who have had a full conversion window are counted"
              : "Recent entrants are included even though their window has not closed"
          }
          className={cn(
            "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
            matureOnly
              ? "bg-tg-primary/20 text-tg-accent"
              : "text-tg-text-secondary hover:bg-tg-overlay/5",
          )}
        >
          <Filter size={13} />
          Settled cohorts only
        </button>
      </div>

      {isLoading && <ChartSkeleton />}

      {!isLoading && data && data.total_entered === 0 && (
        <EmptyState
          icon={TrendingDown}
          title="Nobody entered this funnel"
          description={`No user performed "${funnel.steps[0]}" in the selected period. If the bot has never reported that event, check the step name against what it actually sends.`}
          className="py-16"
        />
      )}

      {!isLoading && data && data.total_entered > 0 && (
        <>
          <GlassCard className="p-6">
            <FunnelChart
              steps={data.steps}
              totalEntered={data.total_entered}
            />
          </GlassCard>

          <GlassCard className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-tg-overlay/5 text-left text-xs text-tg-text-muted">
                  <th className="px-4 py-3 font-medium">Step</th>
                  <th className="px-4 py-3 text-right font-medium">Users</th>
                  <th className="px-4 py-3 text-right font-medium">
                    From previous
                  </th>
                  <th className="px-4 py-3 text-right font-medium">
                    From first
                  </th>
                  <th className="px-4 py-3 text-right font-medium">
                    Median time
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.steps.map((step) => {
                  const dropped =
                    step.position > 0
                      ? data.steps[step.position - 1]!.users - step.users
                      : 0;

                  return (
                    <tr
                      key={`${step.name}-${step.position}`}
                      className="border-b border-tg-overlay/5 last:border-0"
                    >
                      <td className="px-4 py-3">
                        <span className="mr-2 text-xs text-tg-text-muted">
                          {step.position + 1}
                        </span>
                        <span className="font-medium">{step.name}</span>
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        {step.users.toLocaleString()}
                        {dropped > 0 && (
                          <span className="ml-2 text-xs text-tg-red">
                            −{dropped.toLocaleString()}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-tg-text-secondary">
                        {formatPercent(step.conversion_from_previous)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-tg-text-secondary">
                        {formatPercent(step.conversion_from_first)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-tg-text-secondary">
                        {formatDuration(step.median_seconds_from_previous)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </GlassCard>

          <p className="text-xs text-tg-text-muted">
            {data.total_entered.toLocaleString()} users entered within a{" "}
            {formatDuration(data.window_seconds)} conversion window.{" "}
            {matureOnly
              ? "Only entrants whose window has fully closed are counted."
              : "Recent entrants are included, so the last steps may still fill in."}{" "}
            A dash means there was no data to divide by, which is not the same
            as 0%.
          </p>
        </>
      )}
    </div>
  );
}
