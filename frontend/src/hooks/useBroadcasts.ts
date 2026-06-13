import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { broadcastsApi } from "@/api/broadcasts";
import type { BroadcastCreateRequest } from "@/types/api";

export function useCreateBroadcast() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: BroadcastCreateRequest) => broadcastsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["broadcasts"] });
      toast.success("Broadcast created");
    },
  });
}

export function useSendBroadcast() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => broadcastsApi.send(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["broadcasts"] });
      toast.success("Broadcast launched");
    },
  });
}

export function useBroadcastStats(broadcastId: string | null, poll = false) {
  return useQuery({
    queryKey: ["broadcast-stats", broadcastId],
    queryFn: () => broadcastsApi.stats(broadcastId!).then((r) => r.data),
    enabled: !!broadcastId,
    refetchInterval: poll ? 3_000 : false,
  });
}
