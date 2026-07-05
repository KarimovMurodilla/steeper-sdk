import { useState } from "react";
import { Radio, Clock, Send, BarChart2 } from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  useBroadcasts,
  useSendBroadcast,
  useBroadcastStats,
} from "@/hooks/useBroadcasts";
import { formatDate, humanizeLabel } from "@/lib/utils";
import type { BroadcastListItem, BroadcastStatus } from "@/types/api";

const STATUS_VARIANT: Record<
  BroadcastStatus,
  "success" | "warning" | "danger" | "info" | "neutral"
> = {
  draft: "neutral",
  scheduled: "info",
  processing: "warning",
  sent: "success",
  failed: "danger",
  cancelled: "neutral",
};

interface Props {
  botId: string;
}

export function BroadcastList({ botId }: Props) {
  const { data, isLoading } = useBroadcasts(botId);
  const broadcasts = data?.items ?? [];

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  if (broadcasts.length === 0) {
    return (
      <EmptyState
        icon={Radio}
        title="No broadcasts yet"
        description="Create your first broadcast to reach all your bot users at once."
        className="py-20"
      />
    );
  }

  return (
    <div className="space-y-3">
      {broadcasts.map((b) => (
        <BroadcastRow key={b.id} broadcast={b} />
      ))}
    </div>
  );
}

function BroadcastRow({ broadcast }: { broadcast: BroadcastListItem }) {
  const [showStats, setShowStats] = useState(false);
  const sendMutation = useSendBroadcast();

  const canLaunch =
    broadcast.status === "draft" || broadcast.status === "scheduled";

  return (
    <GlassCard className="p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex items-center gap-2">
            <Badge variant={STATUS_VARIANT[broadcast.status]}>
              {humanizeLabel(broadcast.status)}
            </Badge>
            {broadcast.scheduled_at && (
              <span className="inline-flex items-center gap-1 text-xs text-tg-text-muted">
                <Clock size={12} />
                {formatDate(broadcast.scheduled_at)}
              </span>
            )}
          </div>
          <p className="line-clamp-2 text-sm text-tg-text">
            {broadcast.message_content}
          </p>
          <p className="mt-1.5 text-xs text-tg-text-muted">
            Created {formatDate(broadcast.created_at)}
          </p>
        </div>

        <div className="flex shrink-0 flex-col gap-2">
          {canLaunch && (
            <Button
              size="sm"
              onClick={() => sendMutation.mutate(broadcast.id)}
              loading={sendMutation.isPending}
            >
              <Send size={14} />
              Launch
            </Button>
          )}
          <Button
            size="sm"
            variant="secondary"
            onClick={() => setShowStats((s) => !s)}
          >
            <BarChart2 size={14} />
            Stats
          </Button>
        </div>
      </div>

      {showStats && <BroadcastRowStats broadcastId={broadcast.id} />}
    </GlassCard>
  );
}

function BroadcastRowStats({ broadcastId }: { broadcastId: string }) {
  const { data, isLoading } = useBroadcastStats(broadcastId, true);

  if (isLoading) {
    return (
      <div className="mt-4 flex justify-center border-t border-white/5 pt-4">
        <Spinner />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="mt-4 grid grid-cols-3 gap-3 border-t border-white/5 pt-4">
      <StatBox label="Total" value={data.total} color="text-tg-accent" />
      <StatBox label="Sent" value={data.sent} color="text-tg-green" />
      <StatBox label="Failed" value={data.failed} color="text-tg-red" />
    </div>
  );
}

function StatBox({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/5 p-3 text-center">
      <p className={`text-xl font-bold ${color}`}>{value.toLocaleString()}</p>
      <p className="mt-1 text-xs text-tg-text-muted">{label}</p>
    </div>
  );
}
