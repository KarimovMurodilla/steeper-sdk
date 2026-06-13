import { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useUpdateBot } from "@/hooks/useBots";
import type { BotViewModel } from "@/types/api";

interface Props {
  open: boolean;
  onClose: () => void;
  bot: BotViewModel | null;
}

export function EditBotModal({ open, onClose, bot }: Props) {
  const [token, setToken] = useState("");
  const mutation = useUpdateBot();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!bot || !token.trim()) return;
    mutation.mutate(
      { id: bot.id, data: { token: token.trim() } },
      {
        onSuccess: () => {
          setToken("");
          onClose();
        },
      },
    );
  };

  return (
    <Modal open={open} onClose={onClose} title={`Edit: ${bot?.name ?? "Bot"}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="New Token"
          placeholder="Paste new token from @BotFather"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          autoFocus
        />
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose} type="button">
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            Update
          </Button>
        </div>
      </form>
    </Modal>
  );
}
