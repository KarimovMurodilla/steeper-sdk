import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { logsApi } from "@/api/logs";
import { useWebSocket } from "@/hooks/useWebSocket";
import type {
  BotLogQueryParams,
  BotLogViewModel,
  LogLevel,
} from "@/types/api";
import type { WSBotLogCreatedData, WSDownlinkEnvelope } from "@/types/ws";

export const PAGE_SIZE = 100;

/**
 * How many live records are kept in memory. A busy bot can emit thousands per
 * minute; without a ceiling an open tab would grow until it stalls.
 */
export const LIVE_BUFFER_MAX = 1_000;

export interface LogFilters {
  levels: LogLevel[];
  search: string;
  loggerName: string;
}

export const EMPTY_FILTERS: LogFilters = {
  levels: [],
  search: "",
  loggerName: "",
};

function toQueryParams(filters: LogFilters): BotLogQueryParams {
  return {
    limit: PAGE_SIZE,
    ...(filters.levels.length > 0 ? { level: filters.levels } : {}),
    ...(filters.search ? { search: filters.search } : {}),
    ...(filters.loggerName ? { logger_name: filters.loggerName } : {}),
  };
}

/** Client-side mirror of the server's filters, applied to live records. */
function matchesFilters(record: BotLogViewModel, filters: LogFilters): boolean {
  if (filters.levels.length > 0 && !filters.levels.includes(record.level)) {
    return false;
  }
  if (filters.search && !record.message.includes(filters.search)) {
    return false;
  }
  if (filters.loggerName && !record.logger.startsWith(filters.loggerName)) {
    return false;
  }
  return true;
}

/**
 * Log history plus the live tail for one bot.
 *
 * History is paginated from the API; new records arrive over the WebSocket and
 * are held in a separate buffer instead of invalidating the query — refetching
 * a hundred rows on every incoming batch would put the panel in a permanent
 * loading loop on a busy bot.
 *
 * Records are keyed by `cursor` (a Loki nanosecond timestamp), which is not
 * guaranteed unique: two records can share a nanosecond, and a page boundary
 * can hand the same record back twice. De-duplication therefore keys on
 * cursor + message.
 */
export function useLogs(botId: string | null, filters: LogFilters) {
  const [live, setLive] = useState<BotLogViewModel[]>([]);
  const [paused, setPaused] = useState(false);

  // Read inside the socket handler without making it a dependency: a changed
  // handler identity would not reconnect the socket, but it would re-run the
  // subscribe effect on every keystroke in the filter input.
  const filtersRef = useRef(filters);
  filtersRef.current = filters;
  const pausedRef = useRef(paused);
  pausedRef.current = paused;

  const query = useInfiniteQuery({
    queryKey: ["logs", botId, filters.levels, filters.search, filters.loggerName],
    queryFn: ({ pageParam }) =>
      logsApi
        .listLogs(botId!, {
          ...toQueryParams(filters),
          ...(pageParam ? { cursor: pageParam as string } : {}),
        })
        .then((r) => r.data),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled: !!botId,
    staleTime: 5_000,
  });

  const handleWSMessage = useCallback(
    (envelope: WSDownlinkEnvelope) => {
      if (envelope.event !== "bot.log.created") return;
      if (!botId || envelope.bot_id !== botId) return;
      if (pausedRef.current) return;

      const { records } = envelope.data as unknown as WSBotLogCreatedData;
      const accepted = records.filter((r) => matchesFilters(r, filtersRef.current));
      if (accepted.length === 0) return;

      setLive((prev) => {
        // The backend ships a batch oldest-first; the view is newest-first.
        const next = [...accepted].reverse().concat(prev);
        return next.length > LIVE_BUFFER_MAX
          ? next.slice(0, LIVE_BUFFER_MAX)
          : next;
      });
    },
    [botId],
  );

  const { subscribe, unsubscribe } = useWebSocket(handleWSMessage);

  useEffect(() => {
    if (!botId) return;
    subscribe("bot_id", botId, "logs");
    return () => {
      unsubscribe("bot_id", botId, "logs");
    };
  }, [botId, subscribe, unsubscribe]);

  // Filters are part of the query key, so history refetches on its own; the
  // live buffer holds records matched against the previous filters and has to
  // be dropped by hand.
  useEffect(() => {
    setLive([]);
  }, [botId, filters.levels, filters.search, filters.loggerName]);

  const records = useMemo(() => {
    const history = query.data?.pages.flatMap((page) => page.items) ?? [];
    const seen = new Set<string>();
    const merged: BotLogViewModel[] = [];

    for (const record of [...live, ...history]) {
      const key = `${record.cursor}:${record.message}`;
      if (seen.has(key)) continue;
      seen.add(key);
      merged.push(record);
    }

    return merged;
  }, [live, query.data]);

  const { refetch } = query;
  const resume = useCallback(() => {
    setPaused(false);
    // Anything emitted while paused was dropped, so history is the only source
    // of truth for that gap.
    setLive([]);
    void refetch();
  }, [refetch]);

  return {
    records,
    liveCount: live.length,
    paused,
    pause: () => setPaused(true),
    resume,
    isLoading: query.isLoading,
    isError: query.isError,
    hasNextPage: query.hasNextPage,
    isFetchingNextPage: query.isFetchingNextPage,
    fetchNextPage: query.fetchNextPage,
    refetch,
  };
}
