import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { botsApi } from "@/api/bots";
import type { BotCreateRequest, BotUpdateRequest } from "@/types/api";

export function useBots(page = 1, size = 20) {
  return useQuery({
    queryKey: ["bots", page, size],
    queryFn: () => botsApi.list(page, size).then((r) => r.data),
    staleTime: 30_000,
  });
}

export function useCreateBot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: BotCreateRequest) => botsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bots"] });
      toast.success("Bot added successfully");
    },
  });
}

export function useUpdateBot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: BotUpdateRequest }) =>
      botsApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bots"] });
      toast.success("Bot updated");
    },
  });
}

export function useDeleteBot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => botsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bots"] });
      toast.success("Bot deleted");
    },
  });
}
