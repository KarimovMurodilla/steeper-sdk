import { useState } from "react";
import { Bot, Plus } from "lucide-react";
import { useActiveBot } from "@/hooks/useActiveBot";
import { BroadcastList } from "@/components/Broadcast/BroadcastList";
import { CreateBroadcastModal } from "@/components/Broadcast/CreateBroadcastModal";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";

export function BroadcastsPage() {
  const { activeBotId, bots, isLoading } = useActiveBot();
  const activeBot = bots.find((b) => b.id === activeBotId) ?? null;
  const [createOpen, setCreateOpen] = useState(false);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Broadcasts</h1>
          <p className="text-sm text-tg-text-secondary mt-1">
            Send mass messages to your bot users
          </p>
        </div>
        {activeBot && (
          <Button onClick={() => setCreateOpen(true)}>
            <Plus size={16} />
            Create Broadcast
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : !activeBot ? (
        <EmptyState
          icon={Bot}
          title="No bot selected"
          description="Add or select a bot from the switcher to send a broadcast."
          className="py-24"
        />
      ) : (
        <>
          <BroadcastList botId={activeBot.id} />
          <CreateBroadcastModal
            open={createOpen}
            onClose={() => setCreateOpen(false)}
            bot={activeBot}
          />
        </>
      )}
    </div>
  );
}
