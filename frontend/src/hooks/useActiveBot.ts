import { useEffect } from "react";
import { useBots } from "./useBots";
import { useUIStore } from "@/store/uiStore";

/**
 * Resolves the active bot, auto-selecting the first available one when none is
 * chosen yet. Keeps Chats / Analytics usable without bouncing through the Bots
 * page first.
 */
export function useActiveBot() {
  const { activeBotId, setActiveBotId } = useUIStore();
  const { data, isLoading } = useBots(1, 100);
  const bots = data?.items ?? [];

  useEffect(() => {
    if (isLoading) return;
    if (!activeBotId && bots.length > 0) {
      setActiveBotId(bots[0]!.id);
    }
  }, [activeBotId, bots, isLoading, setActiveBotId]);

  return { activeBotId, bots, isLoading };
}
