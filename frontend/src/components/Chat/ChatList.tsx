import { cn, displayName, formatDate, truncate } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";
import { useChatList } from "@/hooks/useChats";
import { Avatar } from "@/components/ui/Avatar";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { MessageSquare } from "lucide-react";

export function ChatList() {
  const { activeBotId, activeChatId, setActiveChatId, setMobileChatOpen } =
    useUIStore();
  const { data, isLoading } = useChatList(activeBotId);

  if (!activeBotId) {
    return (
      <EmptyState
        icon={MessageSquare}
        title="Select a bot"
        description="Choose a bot from the Bots page to view chats"
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
        icon={MessageSquare}
        title="No chats yet"
        description="Chats will appear here when users message the bot"
        className="h-full"
      />
    );
  }

  return (
    <div className="flex flex-col overflow-y-auto">
      {data.items.map((chat) => {
        const name = displayName(chat.first_name, null, chat.username);
        return (
          <button
            key={chat.chat_id}
            onClick={() => {
              setActiveChatId(chat.chat_id);
              setMobileChatOpen(true);
            }}
            className={cn(
              "flex items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-tg-surface-hover",
              activeChatId === chat.chat_id && "bg-tg-surface",
            )}
          >
            <Avatar name={name} size="md" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="truncate text-sm font-medium">{name}</span>
                <span className="flex-shrink-0 text-xs text-tg-text-muted">
                  {formatDate(chat.updated_at)}
                </span>
              </div>
              {chat.last_message && (
                <p className="truncate text-sm text-tg-text-secondary mt-0.5">
                  {truncate(chat.last_message, 50)}
                </p>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}
