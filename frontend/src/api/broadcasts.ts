import { apiClient } from "./client";
import type {
  BroadcastCreateRequest,
  BroadcastResponse,
  BroadcastStatsResponse,
  SuccessResponse,
} from "@/types/api";

export const broadcastsApi = {
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
