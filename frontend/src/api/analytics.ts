import { apiClient } from "./client";
import type {
  BotAnalyticsSummary,
  BotUpdateStats,
  HealthCheckResponse,
  UpdateStatsParams,
} from "@/types/api";

export const analyticsApi = {
  summary(botId: string) {
    return apiClient.get<BotAnalyticsSummary>(
      `/v1/bots/${botId}/analytics/summary`,
    );
  },

  updates(botId: string, params: UpdateStatsParams = {}) {
    return apiClient.get<BotUpdateStats>(
      `/v1/bots/${botId}/analytics/updates`,
      { params },
    );
  },

  health() {
    return apiClient.get<HealthCheckResponse>("/health/");
  },
};
