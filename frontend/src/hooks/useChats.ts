import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { chatsApi } from "@/api/chats";
import type { SendMessageRequest } from "@/types/api";

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

export function useSendMessage(botId: string, chatId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SendMessageRequest) =>
      chatsApi.sendMessage(botId, chatId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["messages", botId, chatId] });
      qc.invalidateQueries({ queryKey: ["chats", botId] });
    },
  });
}
