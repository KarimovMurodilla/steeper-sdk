import { useBots } from "@/hooks/useBots";
import { BroadcastForm } from "@/components/Broadcast/BroadcastForm";
import { BroadcastStats } from "@/components/Broadcast/BroadcastStats";
import { Spinner } from "@/components/ui/Spinner";

export function BroadcastsPage() {
  const { data, isLoading } = useBots(1, 100);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Broadcasts</h1>
        <p className="text-sm text-tg-text-secondary mt-1">
          Send mass messages to your bot users
        </p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : (
        <div className="space-y-6">
          <BroadcastForm bots={data?.items ?? []} />
          <BroadcastStats />
        </div>
      )}
    </div>
  );
}
