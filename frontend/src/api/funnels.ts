import { apiClient } from "./client";
import type {
  EventName,
  FunnelCreateRequest,
  FunnelReport,
  FunnelReportParams,
  FunnelUpdateRequest,
  FunnelViewModel,
} from "@/types/api";

export const funnelsApi = {
  list(botId: string) {
    return apiClient.get<FunnelViewModel[]>(`/v1/bots/${botId}/funnels`);
  },

  create(botId: string, data: FunnelCreateRequest) {
    return apiClient.post<FunnelViewModel>(`/v1/bots/${botId}/funnels`, data);
  },

  update(botId: string, funnelId: string, data: FunnelUpdateRequest) {
    return apiClient.patch<FunnelViewModel>(
      `/v1/bots/${botId}/funnels/${funnelId}`,
      data,
    );
  },

  remove(botId: string, funnelId: string) {
    return apiClient.delete(`/v1/bots/${botId}/funnels/${funnelId}`);
  },

  report(botId: string, funnelId: string, params: FunnelReportParams = {}) {
    return apiClient.get<FunnelReport>(
      `/v1/bots/${botId}/funnels/${funnelId}/report`,
      { params },
    );
  },

  /** Event names the bot has actually sent, for the step builder. */
  eventNames(botId: string) {
    return apiClient.get<EventName[]>(`/v1/bots/${botId}/events/names`);
  },
};
