import { useState, useRef, useCallback, useLayoutEffect } from "react";
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

  // Grow the composer with its content up to the CSS max height, then scroll.
  useLayoutEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [text]);

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed) return;
    // The optimistic bubble appears at once, so the composer clears right away
    // instead of waiting for the round-trip.
    mutation.mutate({ text: trimmed, clientId: crypto.randomUUID() });
    setText("");
    inputRef.current?.focus();
  }, [text, mutation]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-tg-overlay/5 bg-tg-bg-secondary/80 backdrop-blur-[20px] px-4 py-3">
      <div className="flex items-end gap-2">
        <textarea
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Write a message..."
          aria-label="Message"
          rows={1}
          className="max-h-32 flex-1 resize-none overflow-y-auto rounded-xl border border-tg-overlay/10 bg-tg-overlay/5 px-4 py-2.5 text-sm text-tg-text transition-colors placeholder:text-tg-text-muted outline-none focus:border-tg-primary focus:ring-1 focus:ring-tg-primary/30"
          style={{ minHeight: "40px" }}
        />
        <button
          onClick={handleSend}
          disabled={!text.trim()}
          aria-label="Send message"
          className={cn(
            "flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tg-accent disabled:cursor-not-allowed",
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
