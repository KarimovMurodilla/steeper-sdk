import { Clock, RotateCw, TriangleAlert, X } from "lucide-react";
import { cn, formatTime } from "@/lib/utils";
import type { OutboxMessage } from "@/store/outboxStore";

interface Props {
  message: OutboxMessage;
  onRetry: () => void;
  onDiscard: () => void;
}

/** An admin message that the server has not confirmed yet. */
export function OutboxBubble({ message, onRetry, onDiscard }: Props) {
  const failed = message.status === "failed";

  return (
    <div className="flex animate-fade-in justify-end">
      <div
        className={cn(
          "max-w-[75%] rounded-2xl rounded-br-md px-4 py-2 shadow-sm transition-colors",
          failed
            ? "border border-tg-red/40 bg-tg-red/10"
            : "bg-tg-msg-out opacity-70",
        )}
      >
        <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
          {message.text}
        </p>
        <div className="mt-1 flex items-center justify-end gap-2">
          {failed ? (
            <>
              <span className="flex items-center gap-1 text-[11px] text-tg-red">
                <TriangleAlert size={11} />
                Not sent
              </span>
              <button
                onClick={onRetry}
                aria-label="Retry sending message"
                className="flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] text-tg-accent transition-colors hover:bg-tg-overlay/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tg-accent"
              >
                <RotateCw size={11} />
                Retry
              </button>
              <button
                onClick={onDiscard}
                aria-label="Discard message"
                className="flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] text-tg-text-muted transition-colors hover:bg-tg-overlay/10 hover:text-tg-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tg-accent"
              >
                <X size={11} />
                Discard
              </button>
            </>
          ) : (
            <span className="flex items-center gap-1 text-[11px] text-tg-text-muted">
              <Clock size={11} />
              {formatTime(message.createdAt)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
