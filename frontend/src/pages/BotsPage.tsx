import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Bot } from "lucide-react";
import { useBots, useUpdateBot, useDeleteBot } from "@/hooks/useBots";
import { useUIStore } from "@/store/uiStore";
import { BotCard } from "@/components/Bot/BotCard";
import { AddBotModal } from "@/components/Bot/AddBotModal";
import { EditBotModal } from "@/components/Bot/EditBotModal";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import type { BotViewModel } from "@/types/api";

export function BotsPage() {
  const [addOpen, setAddOpen] = useState(false);
  const [editBot, setEditBot] = useState<BotViewModel | null>(null);
  const { data, isLoading } = useBots();
  const updateBot = useUpdateBot();
  const deleteBot = useDeleteBot();
  const { setActiveBotId } = useUIStore();
  const navigate = useNavigate();

  const handleSelect = (id: string) => {
    setActiveBotId(id);
    navigate("/chats");
  };

  const handleToggle = (bot: BotViewModel) => {
    updateBot.mutate({
      id: bot.id,
      data: { status: bot.status === "active" ? "disabled" : "active" },
    });
  };

  const handleDelete = (id: string) => {
    if (window.confirm("Are you sure you want to delete this bot?")) {
      deleteBot.mutate(id);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Bots</h1>
          <p className="text-sm text-tg-text-secondary mt-1">
            Manage your connected Telegram bots
          </p>
        </div>
        <Button onClick={() => setAddOpen(true)}>
          <Plus size={16} />
          Add Bot
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : !data?.items.length ? (
        <EmptyState
          icon={Bot}
          title="No bots connected"
          description="Add your first Telegram bot to get started"
          action={
            <Button onClick={() => setAddOpen(true)}>
              <Plus size={16} />
              Add Bot
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {data.items.map((bot) => (
            <BotCard
              key={bot.id}
              bot={bot}
              onSelect={handleSelect}
              onEdit={setEditBot}
              onDelete={handleDelete}
              onToggle={handleToggle}
            />
          ))}
        </div>
      )}

      {data && data.pages > 1 && (
        <div className="mt-6 text-center text-sm text-tg-text-muted">
          Page {data.page} of {data.pages} &middot; {data.total} bots total
        </div>
      )}

      <AddBotModal open={addOpen} onClose={() => setAddOpen(false)} />
      <EditBotModal
        open={!!editBot}
        onClose={() => setEditBot(null)}
        bot={editBot}
      />
    </div>
  );
}
