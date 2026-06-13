import { apiClient } from "./client";
import type {
  BotCreateRequest,
  BotUpdateRequest,
  BotViewModel,
  PaginatedResponse,
} from "@/types/api";

export const botsApi = {
  list(page = 1, size = 20) {
    return apiClient.get<PaginatedResponse<BotViewModel>>("/v1/bots/", {
      params: { page, size },
    });
  },

  create(data: BotCreateRequest) {
    return apiClient.post<BotViewModel>("/v1/bots/", data);
  },

  update(botId: string, data: BotUpdateRequest) {
    return apiClient.patch<BotViewModel>(`/v1/bots/${botId}`, data);
  },

  delete(botId: string) {
    return apiClient.delete(`/v1/bots/${botId}`);
  },
};
