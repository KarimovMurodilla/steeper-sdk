import { useEffect, useRef, useCallback, useMemo } from "react";
import { ArrowLeft } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { useUIStore } from "@/store/uiStore";
import { useMessages, useChatList } from "@/hooks/useChats";
import { useWebSocket } from "@/hooks/useWebSocket";
import { MessageBubble } from "./MessageBubble";
import { MessageInput } from "./MessageInput";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Avatar } from "@/components/ui/Avatar";
import { MessageSquare } from "lucide-react";
import { displayName } from "@/lib/utils";
import type { WSDownlinkEnvelope } from "@/types/ws";

export function ChatWindow() {
  const {
    activeBotId,
    activeChatId,
    mobileChatOpen,
    setMobileChatOpen,
    setActiveChatId,
  } = useUIStore();
  const queryClient = useQueryClient();
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useMessages(activeBotId, activeChatId);

  const { data: chatListData } = useChatList(activeBotId);
  const activeChat = chatListData?.items.find(
    (c) => c.chat_id === activeChatId,
  );
  const chatName = activeChat
    ? displayName(activeChat.first_name, null, activeChat.username)
    : "Chat";

  const handleWSMessage = useCallback(
    (envelope: WSDownlinkEnvelope) => {
      if (envelope.bot_id !== activeBotId) return;

      // A new chat or any new message changes the chat list (ordering / unread /
      // a brand-new conversation appearing), so refresh it regardless of which
      // chat is currently open.
      if (
        envelope.event === "chat.created" ||
        envelope.event === "chat.message.created"
      ) {
        queryClient.invalidateQueries({
          queryKey: ["chats", activeBotId],
        });
      }

      // Only the currently open chat needs its message history refreshed.
      if (
        envelope.event === "chat.message.created" &&
        envelope.chat_id === activeChatId
      ) {
        queryClient.invalidateQueries({
          queryKey: ["messages", activeBotId, activeChatId],
        });
      }
    },
    [activeBotId, activeChatId, queryClient],
  );

  const { subscribe, unsubscribe } = useWebSocket(handleWSMessage);

  // Subscribe to the bot for its whole lifetime (drives the chat list), not per
  // chat — otherwise switching chats within a bot briefly unsubscribes the bot
  // and bot-level events (e.g. chat.created) are lost.
  useEffect(() => {
    if (!activeBotId) return;
    subscribe("bot_id", activeBotId);
    return () => {
      unsubscribe("bot_id", activeBotId);
    };
  }, [activeBotId, subscribe, unsubscribe]);

  useEffect(() => {
    if (!activeChatId) return;
    subscribe("chat_id", activeChatId);
    return () => {
      unsubscribe("chat_id", activeChatId);
    };
  }, [activeChatId, subscribe, unsubscribe]);

  const messages = useMemo(
    () =>
      data?.pages
        .flatMap((p) => p.items)
        .slice()
        .reverse() ?? [],
    [data],
  );

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const handleScroll = useCallback(() => {
    const el = scrollContainerRef.current;
    if (!el || !hasNextPage || isFetchingNextPage) return;
    if (el.scrollTop < 100) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  if (!activeBotId || !activeChatId) {
    return (
      <EmptyState
        icon={MessageSquare}
        title="Select a chat"
        description="Choose a conversation from the list to start messaging"
        className="h-full"
      />
    );
  }

  return (
    <div
      className={`flex h-full flex-col ${mobileChatOpen ? "flex" : "hidden"} lg:flex`}
    >
      <div className="flex items-center gap-3 border-b border-white/5 bg-tg-bg-secondary/80 backdrop-blur-[20px] px-4 py-3">
        <button
          onClick={() => {
            setMobileChatOpen(false);
            setActiveChatId(null);
          }}
          className="rounded-lg p-1.5 text-tg-text-secondary hover:bg-white/10 lg:hidden"
        >
          <ArrowLeft size={20} />
        </button>
        <Avatar name={chatName} size="sm" />
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold">{chatName}</h3>
          {activeChat?.username && (
            <p className="truncate text-xs text-tg-text-muted">
              @{activeChat.username}
            </p>
          )}
        </div>
      </div>

      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-2"
      >
        {isFetchingNextPage && (
          <div className="flex justify-center py-2">
            <Spinner size="sm" />
          </div>
        )}
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <Spinner />
          </div>
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}
        <div ref={bottomRef} />
      </div>

      <MessageInput botId={activeBotId} chatId={activeChatId} />
    </div>
  );
}
