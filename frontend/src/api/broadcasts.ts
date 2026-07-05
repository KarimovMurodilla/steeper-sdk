import { apiClient } from "./client";
import type {
  BroadcastCreateRequest,
  BroadcastListItem,
  BroadcastResponse,
  BroadcastStatsResponse,
  BroadcastStatus,
  PaginatedResponse,
  SuccessResponse,
} from "@/types/api";

export const broadcastsApi = {
  list(params: {
    bot_id?: string | null;
    status?: BroadcastStatus | null;
    page?: number;
    size?: number;
  }) {
    return apiClient.get<PaginatedResponse<BroadcastListItem>>(
      "/v1/broadcasts/",
      {
        params: {
          bot_id: params.bot_id || undefined,
          status: params.status || undefined,
          page: params.page ?? 1,
          size: params.size ?? 20,
        },
      },
    );
  },

  create(data: BroadcastCreateRequest) {
    return apiClient.post<BroadcastResponse>("/v1/broadcasts/", data);
  },

  send(broadcastId: string) {
    return apiClient.post<SuccessResponse>(
      `/v1/broadcasts/${broadcastId}/send`,
    );
  },

  stats(broadcastId: string) {
    return apiClient.get<BroadcastStatsResponse>(
      `/v1/broadcasts/${broadcastId}/stats`,
    );
  },
};
