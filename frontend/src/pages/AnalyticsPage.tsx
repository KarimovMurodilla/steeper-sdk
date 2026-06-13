import { useBots } from "@/hooks/useBots";
import { useUIStore } from "@/store/uiStore";
import { AnalyticsDashboard } from "@/components/Analytics/AnalyticsDashboard";
import { Spinner } from "@/components/ui/Spinner";

export function AnalyticsPage() {
  const { activeBotId, setActiveBotId } = useUIStore();
  const { data, isLoading } = useBots(1, 100);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-sm text-tg-text-secondary mt-1">
            Monitor your bot performance
          </p>
        </div>
        {!isLoading && data && (
          <select
            value={activeBotId ?? ""}
            onChange={(e) => setActiveBotId(e.target.value || null)}
            className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-tg-text outline-none focus:border-tg-primary transition-colors"
          >
            <option value="">Select a bot...</option>
            {data.items.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : (
        <AnalyticsDashboard botId={activeBotId} />
      )}
    </div>
  );
}
