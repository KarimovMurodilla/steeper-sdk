import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  useCallback,
  useMemo,
} from "react";
import { ArrowLeft, ChevronDown } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { useUIStore } from "@/store/uiStore";
import { useMessages, useChatList, useSendMessage } from "@/hooks/useChats";
import { useWebSocket } from "@/hooks/useWebSocket";
import { MessageBubble } from "./MessageBubble";
import { OutboxBubble } from "./OutboxBubble";
import { MessageInput } from "./MessageInput";
import { Spinner } from "@/components/ui/Spinner";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Avatar } from "@/components/ui/Avatar";
import { MessageSquare } from "lucide-react";
import { displayName, formatDaySeparator, isSameDay } from "@/lib/utils";
import { NO_OUTBOX, useOutboxStore } from "@/store/outboxStore";
import type { WSChatMessageCreatedData, WSDownlinkEnvelope } from "@/types/ws";
import type {
  ChatListItemViewModel,
  CursorPaginatedResponse,
  MessageListItemViewModel,
  PaginatedResponse,
} from "@/types/api";

type MessagePages = {
  pages: CursorPaginatedResponse<MessageListItemViewModel>[];
  pageParams: unknown[];
};

/** Prepends a live message to the newest page, ignoring duplicates. */
function withLiveMessage(
  old: MessagePages | undefined,
  message: MessageListItemViewModel,
): MessagePages | undefined {
  if (!old?.pages.length) return old;
  const seen = old.pages.some((page) =>
    page.items.some((item) => item.id === message.id),
  );
  if (seen) return old;

  const [newest, ...rest] = old.pages;
  return {
    ...old,
    pages: [{ ...newest!, items: [message, ...newest!.items] }, ...rest],
  };
}

/** Moves the chat that just received a message to the top of the list. */
function withLiveChatPreview(
  old: PaginatedResponse<ChatListItemViewModel> | undefined,
  chatId: string,
  preview: string,
  updatedAt: string,
): PaginatedResponse<ChatListItemViewModel> | undefined {
  if (!old) return old;
  const target = old.items.find((chat) => chat.chat_id === chatId);
  if (!target) return old;

  const updated = { ...target, last_message: preview, updated_at: updatedAt };
  return {
    ...old,
    items: [updated, ...old.items.filter((chat) => chat.chat_id !== chatId)],
  };
}

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

  const atBottomRef = useRef(true);
  // Scroll height captured right before an older page is requested, so the
  // viewport can be pinned to the same message once that page is prepended.
  const prependAnchorRef = useRef<number | null>(null);

  const {
    data,
    isLoading,
    isError,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useMessages(activeBotId, activeChatId);

  const { data: chatListData } = useChatList(activeBotId);
  const outbox = useOutboxStore((state) =>
    activeChatId ? (state.messages[activeChatId] ?? NO_OUTBOX) : NO_OUTBOX,
  );
  const removeFromOutbox = useOutboxStore((state) => state.remove);
  const sendMessage = useSendMessage(activeBotId ?? "", activeChatId ?? "");
  const bumpUnread = useUIStore((state) => state.bumpUnread);
  const unreadForChat = useUIStore((state) =>
    activeChatId ? (state.unread[activeChatId] ?? 0) : 0,
  );
  const [atBottom, setAtBottom] = useState(true);
  // How many messages were unread when this chat was opened: the divider must
  // stay put while the user reads, so it is snapshotted, not live.
  const unreadOnOpenRef = useRef(0);
  const activeChat = chatListData?.items.find(
    (c) => c.chat_id === activeChatId,
  );
  const chatName = activeChat
    ? displayName(activeChat.first_name, null, activeChat.username)
    : "Chat";

  const handleWSMessage = useCallback(
    (envelope: WSDownlinkEnvelope) => {
      if (envelope.bot_id !== activeBotId) return;

      // A brand-new conversation is not in any cache yet, so it has to be
      // fetched rather than patched in.
      if (envelope.event === "chat.created") {
        queryClient.invalidateQueries({ queryKey: ["chats", activeBotId] });
        return;
      }

      if (envelope.event !== "chat.message.created" || !envelope.chat_id) {
        return;
      }

      const data = envelope.data as unknown as WSChatMessageCreatedData;
      const createdAt = new Date(envelope.timestamp * 1000).toISOString();

      // A user message landing in a chat the admin is not reading is what the
      // unread badge counts; the admin's own echoes are not.
      if (envelope.chat_id !== activeChatId && data.sender_type === "user") {
        bumpUnread(envelope.chat_id);
      }

      // The payload carries the whole message, so write it straight into the
      // cache instead of paying a refetch round-trip for data we already have.
      if (envelope.chat_id === activeChatId) {
        queryClient.setQueryData<MessagePages>(
          ["messages", activeBotId, activeChatId],
          (old) =>
            withLiveMessage(old, {
              id: data.message_id,
              sender: data.sender_type,
              content: data.text,
              created_at: createdAt,
            }),
        );
      }

      const chatKey = ["chats", activeBotId];
      const before = queryClient.getQueriesData<
        PaginatedResponse<ChatListItemViewModel>
      >({ queryKey: chatKey });

      queryClient.setQueriesData<PaginatedResponse<ChatListItemViewModel>>(
        { queryKey: chatKey },
        (old) =>
          withLiveChatPreview(old, envelope.chat_id!, data.text, createdAt),
      );

      // The chat is not on any cached page (e.g. it fell past page 1): fall
      // back to a refetch so the list still reorders correctly.
      const known = before.some(([, page]) =>
        page?.items.some((chat) => chat.chat_id === envelope.chat_id),
      );
      if (!known) {
        queryClient.invalidateQueries({ queryKey: chatKey });
      }
    },
    [activeBotId, activeChatId, queryClient, bumpUnread],
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

  // Escape mirrors the back arrow on mobile, where the chat covers the list.
  useEffect(() => {
    if (!mobileChatOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      setMobileChatOpen(false);
      setActiveChatId(null);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [mobileChatOpen, setMobileChatOpen, setActiveChatId]);

  const messages = useMemo(
    () =>
      data?.pages
        .flatMap((p) => p.items)
        .slice()
        .reverse() ?? [],
    [data],
  );

  // Pending sends sit below the confirmed history, so they count as content
  // for the "did anything arrive" scroll check.
  const feedLength = messages.length + outbox.length;

  // Snapshot the badge before the store clears it on open, so the "new
  // messages" divider can be placed above the ones that arrived while away.
  useLayoutEffect(() => {
    unreadOnOpenRef.current = Math.min(unreadForChat, 50);
    // Only re-snapshot when the chat itself changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeChatId]);

  // Jump straight to the newest message when a different chat is opened.
  useLayoutEffect(() => {
    atBottomRef.current = true;
    setAtBottom(true);
    prependAnchorRef.current = null;
    const el = scrollContainerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [activeChatId]);

  useLayoutEffect(() => {
    const el = scrollContainerRef.current;
    if (!el) return;

    // Older page prepended: keep the message the user was reading in place
    // instead of yanking the viewport.
    const anchor = prependAnchorRef.current;
    if (anchor !== null) {
      prependAnchorRef.current = null;
      el.scrollTop += el.scrollHeight - anchor;
      return;
    }

    // New message at the bottom: follow it only if the user was already there.
    if (atBottomRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [feedLength]);

  const handleScroll = useCallback(() => {
    const el = scrollContainerRef.current;
    if (!el) return;

    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 150;
    atBottomRef.current = nearBottom;
    setAtBottom(nearBottom);

    if (!hasNextPage || isFetchingNextPage) return;
    if (el.scrollTop < 100) {
      prependAnchorRef.current = el.scrollHeight;
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
      <div className="flex items-center gap-3 border-b border-tg-overlay/5 bg-tg-bg-secondary/80 backdrop-blur-[20px] px-4 py-3">
        <button
          onClick={() => {
            setMobileChatOpen(false);
            setActiveChatId(null);
          }}
          aria-label="Back to chat list"
          className="rounded-lg p-1.5 text-tg-text-secondary hover:bg-tg-overlay/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tg-accent lg:hidden"
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
          <div className="space-y-3" aria-busy="true">
            {[70, 45, 60, 35, 55].map((width, i) => (
              <div
                key={i}
                className={i % 2 ? "flex justify-end" : "flex justify-start"}
              >
                <Skeleton
                  className="h-12 rounded-2xl"
                  style={{ width: `${width}%` }}
                />
              </div>
            ))}
          </div>
        ) : isError ? (
          <ErrorState
            title="Could not load messages"
            description="The message history did not load. Retry, or reopen the chat."
            onRetry={() => refetch()}
            className="h-full"
          />
        ) : (
          <>
            {messages.map((msg, i) => {
              const prev = messages[i - 1];
              const newDay = !prev || !isSameDay(prev.created_at, msg.created_at);
              const firstUnread =
                unreadOnOpenRef.current > 0 &&
                i === messages.length - unreadOnOpenRef.current;

              return (
                <div key={msg.id} className="space-y-2">
                  {newDay && (
                    <div className="flex justify-center py-2">
                      <span className="rounded-full bg-tg-overlay/5 px-3 py-1 text-[11px] font-medium text-tg-text-secondary">
                        {formatDaySeparator(msg.created_at)}
                      </span>
                    </div>
                  )}
                  {firstUnread && (
                    <div className="flex items-center gap-3 py-1">
                      <div className="h-px flex-1 bg-tg-primary/40" />
                      <span className="text-[11px] font-medium uppercase tracking-wide text-tg-accent">
                        New messages
                      </span>
                      <div className="h-px flex-1 bg-tg-primary/40" />
                    </div>
                  )}
                  <MessageBubble message={msg} />
                </div>
              );
            })}
            {outbox.map((msg) => (
              <OutboxBubble
                key={msg.clientId}
                message={msg}
                onRetry={() =>
                  sendMessage.mutate({
                    text: msg.text,
                    clientId: msg.clientId,
                  })
                }
                onDiscard={() => removeFromOutbox(msg.chatId, msg.clientId)}
              />
            ))}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="relative">
        {!atBottom && (
          <button
            onClick={() => {
              atBottomRef.current = true;
              setAtBottom(true);
              bottomRef.current?.scrollIntoView({ behavior: "smooth" });
            }}
            aria-label="Jump to latest messages"
            className="absolute -top-14 right-4 z-10 flex h-10 w-10 items-center justify-center rounded-full border border-tg-overlay/10 bg-tg-surface text-tg-text-secondary shadow-lg transition-colors hover:bg-tg-surface-hover hover:text-tg-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tg-accent"
          >
            <ChevronDown size={20} />
          </button>
        )}
        <MessageInput botId={activeBotId} chatId={activeChatId} />
      </div>
    </div>
  );
}
