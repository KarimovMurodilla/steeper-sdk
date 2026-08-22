import { useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  MessageSquare,
  MessagesSquare,
  Radio,
  User,
  UserMinus,
  UserPlus,
  Users,
  Zap,
} from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatCard } from "./StatCard";
import { AreaChart } from "./charts/AreaChart";
import { BarList } from "./charts/BarList";
import { DonutChart } from "./charts/DonutChart";
import { colorAt } from "./charts/palette";
import {
  useBotAudienceMetrics,
  useBotTrafficMetrics,
} from "@/hooks/useMetrics";
import { cn, displayName, formatCompact } from "@/lib/utils";
import type { TimeGranularity } from "@/types/api";
import { Heatmap } from "./charts/Heatmap";

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

function Panel({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <GlassCard className="p-5">
      <div className="mb-4">
        <h3 className="font-semibold text-tg-text">{title}</h3>
        {hint && <p className="text-xs text-tg-text-muted">{hint}</p>}
      </div>
      {children}
    </GlassCard>
  );
}

function Placeholder({ text, tall }: { text: string; tall?: boolean }) {
  return (
    <div
      className={cn(
        "flex items-center justify-center text-sm text-tg-text-muted",
        tall ? "h-60" : "py-10",
      )}
    >
      {text}
    </div>
  );
}

export function MetricsDashboard({ botId }: Props) {
  const [rangeKey, setRangeKey] = useState("7d");
  const range = RANGES.find((r) => r.key === rangeKey) ?? RANGES[1]!;

  const params = useMemo(
    () => ({
      granularity: range.granularity,
      since: new Date(Date.now() - range.days * 86_400_000).toISOString(),
    }),
    [range.days, range.granularity],
  );

  const { data: traffic, isLoading: trafficLoading } = useBotTrafficMetrics(
    botId,
    params,
  );
  const { data: audience, isLoading: audienceLoading } = useBotAudienceMetrics(
    botId,
    params,
  );

  if (!botId) {
    return (
      <EmptyState
        icon={BarChart3}
        title="No bot selected"
        description="Pick a bot above to explore its metrics."
        className="py-24"
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
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

      {/* ── All-time overview ── */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-tg-text-secondary">
          Overview
        </h2>

        <div className="grid grid-cols-3 gap-3 sm:gap-4">
          <StatCard
            label="Users"
            hint="Total users"
            value={audience?.total_users ?? 0}
            icon={Users}
            color="text-tg-accent"
          />
          <StatCard
            label="Chats"
            hint="Conversations"
            value={traffic?.total_chats ?? 0}
            icon={MessageSquare}
            color="text-tg-green"
          />
          <StatCard
            label="Messages"
            hint="All-time messages"
            value={traffic?.all_time_messages ?? 0}
            icon={MessagesSquare}
            color="text-tg-orange"
          />
        </div>
      </section>

      {/* ── Traffic ── */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-tg-text-secondary">
          Traffic
        </h2>

        <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
          <StatCard
            label="Updates"
            hint="Updates in range"
            value={traffic?.total_updates ?? 0}
            icon={Zap}
            color="text-tg-accent"
          />
          <StatCard
            label="Messages"
            hint="Messages in range"
            value={traffic?.total_messages ?? 0}
            icon={MessagesSquare}
            color="text-tg-green"
          />
          <StatCard
            label="Inbound"
            hint="From users"
            value={
              traffic?.by_sender_type.find((s) => s.label === "user")?.count ?? 0
            }
            icon={Radio}
            color="text-tg-orange"
          />
          <StatCard
            label="Outbound"
            hint="From bot"
            value={
              traffic?.by_sender_type.find((s) => s.label === "bot")?.count ?? 0
            }
            icon={Activity}
            color="text-violet-400"
          />
        </div>

        <Panel title="Update volume" hint="Telegram updates received over time">
          {trafficLoading ? (
            <div className="flex h-60 items-center justify-center">
              <Spinner />
            </div>
          ) : traffic && traffic.timeseries.length > 0 ? (
            <AreaChart
              data={traffic.timeseries}
              granularity={range.granularity}
            />
          ) : (
            <Placeholder text="No activity in this period" tall />
          )}
        </Panel>

        <Panel title="Activity by hour" hint="Weekday and hour of day, local time">
          {trafficLoading ? (
            <div className="flex h-60 items-center justify-center">
              <Spinner />
            </div>
          ) : traffic && traffic.heatmap.length > 0 ? (
            <Heatmap data={traffic.heatmap} />
          ) : (
            <Placeholder text="No activity in this period" tall />
          )}
        </Panel>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Panel title="Update types">
            {traffic && traffic.by_update_type.length > 0 ? (
              <BarList data={traffic.by_update_type} />
            ) : (
              <Placeholder text="No updates in this period" />
            )}
          </Panel>
          <Panel title="Content types">
            {traffic && traffic.by_content_type.length > 0 ? (
              <DonutChart data={traffic.by_content_type} />
            ) : (
              <Placeholder text="No message content in this period" />
            )}
          </Panel>
          <Panel title="Chat types">
            {traffic && traffic.by_chat_type.length > 0 ? (
              <BarList data={traffic.by_chat_type} />
            ) : (
              <Placeholder text="No chats in this period" />
            )}
          </Panel>
        </div>
      </section>

      {/* ── Audience ── */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-tg-text-secondary">
          Audience
        </h2>

        <div className="grid grid-cols-2 gap-3 sm:gap-4">
          <StatCard
            label="New"
            hint="New in range"
            value={audience?.new_users ?? 0}
            icon={UserPlus}
            color="text-tg-green"
          />
          <StatCard
            label="Churned"
            hint="Silent for 30 days"
            value={audience?.churned_users ?? 0}
            icon={UserMinus}
            color="text-tg-red"
          />
        </div>

        <Panel
          title="Active users"
          hint="Rolling windows, measured from now — independent of the range above"
        >
          <div className="flex gap-8">
            {(["dau", "wau", "mau"] as const).map((key, i) => (
              <div key={key}>
                <p
                  className="text-2xl font-bold leading-tight"
                  style={{ color: colorAt(i) }}
                >
                  {formatCompact(audience?.active[key] ?? 0)}
                </p>
                <p className="text-xs uppercase text-tg-text-muted">{key}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="New users" hint="First seen inside the selected range">
          {audienceLoading ? (
            <div className="flex h-60 items-center justify-center">
              <Spinner />
            </div>
          ) : audience && audience.new_users_timeseries.length > 0 ? (
            <AreaChart
              data={audience.new_users_timeseries}
              granularity={range.granularity}
              color={colorAt(2)}
            />
          ) : (
            <Placeholder text="No new users in this period" tall />
          )}
        </Panel>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Panel title="Languages" hint="Telegram language code">
            {audience && audience.by_language.length > 0 ? (
              <BarList data={audience.by_language} />
            ) : (
              <Placeholder text="No language data" />
            )}
          </Panel>

          <Panel title="Most active users" hint="By updates in the range">
            {audience && audience.top_users.length > 0 ? (
              <ul className="space-y-2">
                {audience.top_users.map((u) => (
                  <li
                    key={u.tg_user_id}
                    className="flex items-center justify-between gap-3 text-sm"
                  >
                    <span className="flex min-w-0 items-center gap-2">
                      <User
                        size={14}
                        className="flex-shrink-0 text-tg-text-muted"
                      />
                      <span className="truncate text-tg-text-secondary">
                        {u.first_name || u.username
                          ? displayName(u.first_name, null, u.username)
                          : u.tg_user_id}
                      </span>
                    </span>
                    <span className="font-medium text-tg-text">
                      {u.updates.toLocaleString()}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <Placeholder text="No user activity in this period" />
            )}
          </Panel>
        </div>
      </section>
    </div>
  );
}
