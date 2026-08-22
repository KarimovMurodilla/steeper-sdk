import { apiClient } from "./client";
import type {
  BotAudienceMetrics,
  BotTrafficMetrics,
  HealthCheckResponse,
  MetricsParams,
} from "@/types/api";

export const metricsApi = {
  traffic(botId: string, params: MetricsParams = {}) {
    return apiClient.get<BotTrafficMetrics>(
      `/v1/bots/${botId}/metrics/traffic`,
      { params },
    );
  },

  audience(botId: string, params: MetricsParams = {}) {
    return apiClient.get<BotAudienceMetrics>(
      `/v1/bots/${botId}/metrics/audience`,
      { params },
    );
  },

  health() {
    return apiClient.get<HealthCheckResponse>("/health/");
  },
};
