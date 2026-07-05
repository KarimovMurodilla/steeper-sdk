import { cn, displayName, formatDate, truncate } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";
import { useChatList } from "@/hooks/useChats";
import { Avatar } from "@/components/ui/Avatar";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { MessageSquare, Inbox } from "lucide-react";

export function ChatList() {
  const { activeBotId, activeChatId, setActiveChatId, setMobileChatOpen } =
    useUIStore();
  const { data, isLoading } = useChatList(activeBotId);

  if (!activeBotId) {
    return (
      <EmptyState
        icon={MessageSquare}
        title="No bot selected"
        description="Choose a bot above to view its chats."
        className="h-full"
      />
    );
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (!data?.items.length) {
    return (
      <EmptyState
        icon={Inbox}
        title="No chats yet"
        description="Conversations appear here when users message the bot."
        className="h-full"
      />
    );
  }

  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      {data.items.map((chat) => {
        const name = displayName(chat.first_name, null, chat.username);
        const active = activeChatId === chat.chat_id;
        return (
          <button
            key={chat.chat_id}
            onClick={() => {
              setActiveChatId(chat.chat_id);
              setMobileChatOpen(true);
            }}
            className={cn(
              "flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors",
              active
                ? "bg-tg-primary/15"
                : "hover:bg-tg-surface-hover",
            )}
          >
            <Avatar name={name} size="md" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <span
                  className={cn(
                    "truncate text-sm font-medium",
                    active ? "text-tg-accent" : "text-tg-text",
                  )}
                >
                  {name}
                </span>
                <span className="flex-shrink-0 text-xs text-tg-text-muted">
                  {formatDate(chat.updated_at)}
                </span>
              </div>
              <p className="mt-0.5 truncate text-sm text-tg-text-secondary">
                {chat.last_message
                  ? truncate(chat.last_message, 48)
                  : "No messages yet"}
              </p>
            </div>
          </button>
        );
      })}
    </div>
  );
}
