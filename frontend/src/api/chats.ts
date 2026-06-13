import { apiClient } from "./client";
import type {
  ChatListItemViewModel,
  CursorPaginatedResponse,
  MessageListItemViewModel,
  PaginatedResponse,
  SendMessageRequest,
  SendMessageResponse,
} from "@/types/api";

export const chatsApi = {
  listChats(botId: string, page = 1, size = 30) {
    return apiClient.get<PaginatedResponse<ChatListItemViewModel>>(
      `/v1/bots/${botId}/chats`,
      { params: { page, size } },
    );
  },

  listMessages(botId: string, chatId: string, limit = 50, cursor?: string) {
    return apiClient.get<CursorPaginatedResponse<MessageListItemViewModel>>(
      `/v1/bots/${botId}/chats/${chatId}/messages`,
      { params: { limit, ...(cursor ? { cursor } : {}) } },
    );
  },

  sendMessage(botId: string, chatId: string, data: SendMessageRequest) {
    return apiClient.post<SendMessageResponse>(
      `/v1/bots/${botId}/chats/${chatId}/messages`,
      data,
    );
  },
};
