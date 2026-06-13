import { apiClient } from "./client";
import type { BotAnalyticsSummary, HealthCheckResponse } from "@/types/api";

export const analyticsApi = {
  summary(botId: string) {
    return apiClient.get<BotAnalyticsSummary>(
      `/v1/bots/${botId}/analytics/summary`,
    );
  },

  health() {
    return apiClient.get<HealthCheckResponse>("/health/");
  },
};
