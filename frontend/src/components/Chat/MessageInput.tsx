import { useState, useRef, useCallback } from "react";
import { Send } from "lucide-react";
import { useSendMessage } from "@/hooks/useChats";
import { cn } from "@/lib/utils";

interface Props {
  botId: string;
  chatId: string;
}

export function MessageInput({ botId, chatId }: Props) {
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mutation = useSendMessage(botId, chatId);

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || mutation.isPending) return;
    mutation.mutate(
      { text: trimmed },
      {
        onSuccess: () => {
          setText("");
          inputRef.current?.focus();
        },
      },
    );
  }, [text, mutation]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-white/5 bg-tg-bg-secondary/80 backdrop-blur-[20px] px-4 py-3">
      <div className="flex items-end gap-2">
        <textarea
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Write a message..."
          rows={1}
          className="flex-1 resize-none rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-tg-text placeholder:text-tg-text-muted outline-none focus:border-tg-primary transition-colors max-h-32 overflow-y-auto"
          style={{ minHeight: "40px" }}
        />
        <button
          onClick={handleSend}
          disabled={!text.trim() || mutation.isPending}
          className={cn(
            "flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full transition-colors",
            text.trim()
              ? "bg-tg-primary text-white hover:bg-tg-primary-hover"
              : "text-tg-text-muted",
          )}
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
