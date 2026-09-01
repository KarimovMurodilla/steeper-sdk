import { useMemo, useState } from "react";
import { MessageSquare, Inbox, Search, SearchX, X } from "lucide-react";
import { cn, displayName, formatDate, truncate } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";
import { useChatList } from "@/hooks/useChats";
import { Avatar } from "@/components/ui/Avatar";
import { ChatListSkeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";

export function ChatList() {
  const { activeBotId, activeChatId, setActiveChatId, setMobileChatOpen } =
    useUIStore();
  const unread = useUIStore((state) => state.unread);
  const { data, isLoading, isError, refetch } = useChatList(activeBotId);
  const [query, setQuery] = useState("");

  const items = useMemo(() => data?.items ?? [], [data]);
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return items;
    return items.filter((chat) => {
      const haystack = [chat.first_name, chat.username, chat.last_message]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(needle);
    });
  }, [items, query]);

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
    return <ChatListSkeleton />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Could not load chats"
        description="The chat list did not load. Check your connection and retry."
        onRetry={() => refetch()}
        className="h-full"
      />
    );
  }

  if (!items.length) {
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
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="relative px-3 py-2">
        <Search
          size={15}
          className="pointer-events-none absolute left-6 top-1/2 -translate-y-1/2 text-tg-text-muted"
        />
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search chats"
          aria-label="Search chats"
          className="w-full rounded-lg border border-tg-overlay/10 bg-tg-overlay/5 py-2 pl-9 pr-8 text-sm text-tg-text outline-none transition-colors placeholder:text-tg-text-muted focus:border-tg-primary focus:ring-1 focus:ring-tg-primary/30"
        />
        {query && (
          <button
            onClick={() => setQuery("")}
            aria-label="Clear search"
            className="absolute right-5 top-1/2 -translate-y-1/2 rounded-md p-1 text-tg-text-muted transition-colors hover:bg-tg-overlay/10 hover:text-tg-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tg-accent"
          >
            <X size={13} />
          </button>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <EmptyState
            icon={SearchX}
            title="No matches"
            description={`No chat matches "${query.trim()}".`}
            className="py-12"
          />
        ) : (
          filtered.map((chat) => {
            const name = displayName(chat.first_name, null, chat.username);
            const active = activeChatId === chat.chat_id;
            const unreadCount = unread[chat.chat_id] ?? 0;
            return (
              <button
                key={chat.chat_id}
                aria-current={active ? "true" : undefined}
                onClick={() => {
                  setActiveChatId(chat.chat_id);
                  setMobileChatOpen(true);
                }}
                className={cn(
                  "flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-tg-accent",
                  active ? "bg-tg-primary/15" : "hover:bg-tg-surface-hover",
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
                  <div className="mt-0.5 flex items-center justify-between gap-2">
                    <p className="truncate text-sm text-tg-text-secondary">
                      {chat.last_message
                        ? truncate(chat.last_message, 48)
                        : "No messages yet"}
                    </p>
                    {unreadCount > 0 && !active && (
                      <span
                        aria-label={`${unreadCount} unread messages`}
                        className="flex h-5 min-w-[20px] flex-shrink-0 items-center justify-center rounded-full bg-tg-primary px-1.5 text-[11px] font-semibold text-white"
                      >
                        {unreadCount > 99 ? "99+" : unreadCount}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
