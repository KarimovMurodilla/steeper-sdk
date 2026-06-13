import { cn, formatTime } from "@/lib/utils";
import type { MessageListItemViewModel } from "@/types/api";

interface Props {
  message: MessageListItemViewModel;
}

export function MessageBubble({ message }: Props) {
  const isOutgoing = message.sender === "admin" || message.sender === "bot";

  return (
    <div
      className={cn(
        "flex animate-fade-in",
        isOutgoing ? "justify-end" : "justify-start",
      )}
    >
      <div
        className={cn(
          "max-w-[75%] rounded-2xl px-4 py-2 shadow-sm",
          isOutgoing
            ? "rounded-br-md bg-tg-msg-out"
            : "rounded-bl-md bg-tg-msg-in border border-white/5",
        )}
      >
        {message.sender === "system" && (
          <span className="text-xs font-medium text-tg-accent block mb-0.5">
            System
          </span>
        )}
        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
          {message.content ?? ""}
        </p>
        <div
          className={cn(
            "mt-1 flex items-center gap-1",
            isOutgoing ? "justify-end" : "justify-start",
          )}
        >
          <span className="text-[11px] text-tg-text-muted">
            {formatTime(message.created_at)}
          </span>
        </div>
      </div>
    </div>
  );
}
