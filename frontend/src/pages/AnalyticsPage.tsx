import { Bot } from "lucide-react";
import { useActiveBot } from "@/hooks/useActiveBot";
import { AnalyticsDashboard } from "@/components/Analytics/AnalyticsDashboard";
import { EmptyState } from "@/components/ui/EmptyState";

export function AnalyticsPage() {
  const { activeBotId, bots, isLoading } = useActiveBot();

  return (
    <div className="mx-auto max-w-5xl p-4 sm:p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="mt-1 text-sm text-tg-text-secondary">
          Insights from your Telegram updates
        </p>
      </div>

      {!isLoading && bots.length === 0 ? (
        <EmptyState
          icon={Bot}
          title="No bots connected"
          description="Add a bot from the switcher to start collecting analytics."
          className="py-24"
        />
      ) : (
        <AnalyticsDashboard botId={activeBotId} />
      )}
    </div>
  );
}
