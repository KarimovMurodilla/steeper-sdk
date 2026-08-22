import { useQuery } from "@tanstack/react-query";
import { metricsApi } from "@/api/metrics";
import type { MetricsParams } from "@/types/api";

export function useBotTrafficMetrics(
  botId: string | null,
  params: MetricsParams = {},
) {
  return useQuery({
    queryKey: ["metrics-traffic", botId, params],
    queryFn: () => metricsApi.traffic(botId!, params).then((r) => r.data),
    enabled: !!botId,
    staleTime: 60_000,
  });
}

export function useBotAudienceMetrics(
  botId: string | null,
  params: MetricsParams = {},
) {
  return useQuery({
    queryKey: ["metrics-audience", botId, params],
    queryFn: () => metricsApi.audience(botId!, params).then((r) => r.data),
    enabled: !!botId,
    staleTime: 60_000,
  });
}
