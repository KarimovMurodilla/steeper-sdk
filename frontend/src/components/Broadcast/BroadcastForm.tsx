import { useState } from "react";
import { GlassCard } from "@/components/ui/GlassCard";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useCreateBroadcast, useSendBroadcast } from "@/hooks/useBroadcasts";
import type { BotViewModel } from "@/types/api";

interface Props {
  bots: BotViewModel[];
}

export function BroadcastForm({ bots }: Props) {
  const [botId, setBotId] = useState("");
  const [text, setText] = useState("");
  const [lastActiveDays, setLastActiveDays] = useState("");
  const [scheduleAt, setScheduleAt] = useState("");
  const [broadcastId, setBroadcastId] = useState<string | null>(null);

  const createMutation = useCreateBroadcast();
  const sendMutation = useSendBroadcast();

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!botId || !text.trim()) return;

    createMutation.mutate(
      {
        bot_id: botId,
        text: text.trim(),
        filters: lastActiveDays ? { last_active_days: Number(lastActiveDays) } : null,
        schedule_at: scheduleAt || null,
      },
      {
        onSuccess: ({ data }) => {
          setBroadcastId(data.id);
        },
      },
    );
  };

  const handleSend = () => {
    if (!broadcastId) return;
    sendMutation.mutate(broadcastId);
  };

  return (
    <GlassCard className="p-6 max-w-xl">
      <h3 className="text-lg font-semibold mb-4">Create Broadcast</h3>
      <form onSubmit={handleCreate} className="space-y-4">
        <div className="space-y-1.5">
          <label className="block text-sm text-tg-text-secondary">Bot</label>
          <select
            value={botId}
            onChange={(e) => setBotId(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-tg-text outline-none focus:border-tg-primary transition-colors"
          >
            <option value="">Select a bot...</option>
            {bots
              .filter((b) => b.status === "active")
              .map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
          </select>
        </div>

        <div className="space-y-1.5">
          <label className="block text-sm text-tg-text-secondary">
            Message
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter broadcast message..."
            rows={4}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-tg-text placeholder:text-tg-text-muted outline-none focus:border-tg-primary transition-colors resize-none"
          />
        </div>

        <Input
          label="Active in last N days (optional)"
          type="number"
          min={1}
          value={lastActiveDays}
          onChange={(e) => setLastActiveDays(e.target.value)}
          placeholder="e.g. 7"
        />

        <Input
          label="Schedule (optional)"
          type="datetime-local"
          value={scheduleAt}
          onChange={(e) => setScheduleAt(e.target.value)}
        />

        <div className="flex gap-2 pt-2">
          <Button type="submit" loading={createMutation.isPending}>
            Create Broadcast
          </Button>
          {broadcastId && (
            <Button
              type="button"
              variant="secondary"
              onClick={handleSend}
              loading={sendMutation.isPending}
            >
              Launch Now
            </Button>
          )}
        </div>
      </form>
    </GlassCard>
  );
}
