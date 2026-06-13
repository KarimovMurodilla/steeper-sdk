import { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useCreateBot } from "@/hooks/useBots";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function AddBotModal({ open, onClose }: Props) {
  const [token, setToken] = useState("");
  const mutation = useCreateBot();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) return;
    mutation.mutate(
      { token: token.trim() },
      {
        onSuccess: () => {
          setToken("");
          onClose();
        },
      },
    );
  };

  return (
    <Modal open={open} onClose={onClose} title="Add New Bot">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Bot Token"
          placeholder="Paste token from @BotFather"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          autoFocus
        />
        <p className="text-xs text-tg-text-muted">
          Get a token by talking to{" "}
          <a
            href="https://t.me/BotFather"
            target="_blank"
            rel="noopener noreferrer"
            className="text-tg-accent hover:underline"
          >
            @BotFather
          </a>{" "}
          on Telegram.
        </p>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose} type="button">
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            Add Bot
          </Button>
        </div>
      </form>
    </Modal>
  );
}
