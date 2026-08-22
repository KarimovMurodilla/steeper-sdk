import { Bot } from "lucide-react";
import { useActiveBot } from "@/hooks/useActiveBot";
import { MetricsDashboard } from "@/components/Metrics/MetricsDashboard";
import { EmptyState } from "@/components/ui/EmptyState";

export function MetricsPage() {
  const { activeBotId, bots, isLoading } = useActiveBot();

  return (
    <div className="mx-auto max-w-5xl p-4 sm:p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="mt-1 text-sm text-tg-text-secondary">
          Traffic and audience of your bot
        </p>
      </div>

      {!isLoading && bots.length === 0 ? (
        <EmptyState
          icon={Bot}
          title="No bots connected"
          description="Add a bot from the switcher to start collecting metrics."
          className="py-24"
        />
      ) : (
        <MetricsDashboard botId={activeBotId} />
      )}
    </div>
  );
}
