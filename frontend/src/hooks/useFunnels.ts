import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { funnelsApi } from "@/api/funnels";
import type {
  FunnelCreateRequest,
  FunnelReportParams,
  FunnelUpdateRequest,
} from "@/types/api";

/** Guardrails mirrored from the backend, so the form can reject before the API does. */
export const MIN_FUNNEL_STEPS = 2;
export const MAX_FUNNEL_STEPS = 8;
export const MIN_WINDOW_SECONDS = 60;
export const MAX_WINDOW_SECONDS = 30 * 86_400;

export function useFunnels(botId: string | null) {
  return useQuery({
    queryKey: ["funnels", botId],
    queryFn: () => funnelsApi.list(botId!).then((r) => r.data),
    enabled: !!botId,
  });
}

/**
 * The event names this bot has actually sent.
 *
 * Cached for a while: it is a suggestion list, and re-grouping the event table
 * on every keystroke of the step builder would be a poor trade for a vocabulary
 * that changes when someone ships a new bot version, not by the second.
 */
export function useEventNames(botId: string | null) {
  return useQuery({
    queryKey: ["event-names", botId],
    queryFn: () => funnelsApi.eventNames(botId!).then((r) => r.data),
    enabled: !!botId,
    staleTime: 300_000,
  });
}

export function useFunnelReport(
  botId: string | null,
  funnelId: string | null,
  params: FunnelReportParams = {},
) {
  return useQuery({
    queryKey: ["funnel-report", botId, funnelId, params],
    queryFn: () =>
      funnelsApi.report(botId!, funnelId!, params).then((r) => r.data),
    enabled: !!botId && !!funnelId,
    staleTime: 60_000,
  });
}

export function useCreateFunnel(botId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: FunnelCreateRequest) => funnelsApi.create(botId!, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["funnels"] });
      toast.success("Funnel created");
    },
  });
}

export function useUpdateFunnel(botId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      funnelId,
      data,
    }: {
      funnelId: string;
      data: FunnelUpdateRequest;
    }) => funnelsApi.update(botId!, funnelId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["funnels"] });
      // The definition changed, so every cached report for it is now stale.
      qc.invalidateQueries({ queryKey: ["funnel-report"] });
      toast.success("Funnel updated");
    },
  });
}

export function useDeleteFunnel(botId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (funnelId: string) => funnelsApi.remove(botId!, funnelId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["funnels"] });
      toast.success("Funnel deleted");
    },
  });
}
