import { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useCreateBroadcast } from "@/hooks/useBroadcasts";
import type { BotViewModel } from "@/types/api";

interface Props {
  open: boolean;
  onClose: () => void;
  bot: BotViewModel;
}

export function CreateBroadcastModal({ open, onClose, bot }: Props) {
  const [text, setText] = useState("");
  const [lastActiveDays, setLastActiveDays] = useState("");
  const [scheduleAt, setScheduleAt] = useState("");

  const createMutation = useCreateBroadcast();

  const reset = () => {
    setText("");
    setLastActiveDays("");
    setScheduleAt("");
  };

  const handleClose = () => {
    if (createMutation.isPending) return;
    reset();
    onClose();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    createMutation.mutate(
      {
        bot_id: bot.id,
        text: text.trim(),
        filters: lastActiveDays
          ? { last_active_days: Number(lastActiveDays) }
          : null,
        schedule_at: scheduleAt ? new Date(scheduleAt).toISOString() : null,
      },
      {
        onSuccess: () => {
          reset();
          onClose();
        },
      },
    );
  };

  return (
    <Modal open={open} onClose={handleClose} title="Create Broadcast">
      <p className="mb-4 text-sm text-tg-text-secondary">
        Sending as{" "}
        <span className="font-medium text-tg-text">{bot.name}</span>
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label className="block text-sm text-tg-text-secondary">Message</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter broadcast message..."
            rows={4}
            autoFocus
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

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" type="button" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" loading={createMutation.isPending}>
            Create Broadcast
          </Button>
        </div>
      </form>
    </Modal>
  );
}
