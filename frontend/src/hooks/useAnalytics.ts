import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/api/analytics";

export function useBotAnalytics(botId: string | null) {
  return useQuery({
    queryKey: ["analytics", botId],
    queryFn: () => analyticsApi.summary(botId!).then((r) => r.data),
    enabled: !!botId,
    staleTime: 60_000,
  });
}
