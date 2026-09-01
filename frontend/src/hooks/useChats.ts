import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { chatsApi } from "@/api/chats";
import { useOutboxStore } from "@/store/outboxStore";
import type { SendMessageRequest } from "@/types/api";

export interface SendMessageVariables extends SendMessageRequest {
  /** Ties the request to its optimistic bubble in the outbox. */
  clientId: string;
}

export function useChatList(botId: string | null, page = 1) {
  return useQuery({
    queryKey: ["chats", botId, page],
    queryFn: () => chatsApi.listChats(botId!, page).then((r) => r.data),
    enabled: !!botId,
    staleTime: 15_000,
  });
}

export function useMessages(botId: string | null, chatId: string | null) {
  return useInfiniteQuery({
    queryKey: ["messages", botId, chatId],
    queryFn: ({ pageParam }) =>
      chatsApi
        .listMessages(botId!, chatId!, 50, pageParam as string | undefined)
        .then((r) => r.data),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled: !!botId && !!chatId,
  });
}

/**
 * Sends a message and shows it immediately as an optimistic bubble. The bubble
 * lives in the outbox store until the server confirms it (then the real message
 * arrives over the socket) or the request fails (then it stays, retryable).
 */
export function useSendMessage(botId: string, chatId: string) {
  const qc = useQueryClient();
  const { add, markSending, markFailed, remove } = useOutboxStore();

  return useMutation({
    mutationFn: (variables: SendMessageVariables) =>
      chatsApi.sendMessage(botId, chatId, { text: variables.text }),

    onMutate: ({ clientId, text }) => {
      const existing = useOutboxStore
        .getState()
        .messages[chatId]?.some((m) => m.clientId === clientId);

      // A retry re-uses the bubble that is already on screen.
      if (existing) {
        markSending(chatId, clientId);
        return;
      }

      add({
        clientId,
        chatId,
        text,
        createdAt: new Date().toISOString(),
        status: "sending",
      });
    },

    onError: (_error, { clientId }) => {
      markFailed(chatId, clientId);
    },

    onSuccess: (_data, { clientId }) => {
      remove(chatId, clientId);
      qc.invalidateQueries({ queryKey: ["messages", botId, chatId] });
      qc.invalidateQueries({ queryKey: ["chats", botId] });
    },
  });
}
