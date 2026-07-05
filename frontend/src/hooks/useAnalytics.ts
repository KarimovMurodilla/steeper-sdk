import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/api/analytics";
import type { UpdateStatsParams } from "@/types/api";

export function useBotAnalytics(botId: string | null) {
  return useQuery({
    queryKey: ["analytics", botId],
    queryFn: () => analyticsApi.summary(botId!).then((r) => r.data),
    enabled: !!botId,
    staleTime: 60_000,
  });
}

export function useBotUpdateStats(
  botId: string | null,
  params: UpdateStatsParams = {},
) {
  return useQuery({
    queryKey: ["analytics-updates", botId, params],
    queryFn: () => analyticsApi.updates(botId!, params).then((r) => r.data),
    enabled: !!botId,
    staleTime: 60_000,
  });
}
