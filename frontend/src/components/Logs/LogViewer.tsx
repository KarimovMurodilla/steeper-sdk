import { useCallback, useState } from "react";
import { FileText, TriangleAlert } from "lucide-react";
import { EMPTY_FILTERS, LIVE_BUFFER_MAX, useLogs } from "@/hooks/useLogs";
import type { LogFilters as Filters } from "@/hooks/useLogs";
import { LogFilters } from "./LogFilters";
import { LogRow } from "./LogRow";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";

interface Props {
  botId: string | null;
}

export function LogViewer({ botId }: Props) {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const {
    records,
    liveCount,
    paused,
    pause,
    resume,
    isLoading,
    isError,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
    refetch,
  } = useLogs(botId, filters);

  const handleRefresh = useCallback(() => {
    void refetch();
  }, [refetch]);

  return (
    <div className="flex h-full flex-col">
      <LogFilters
        filters={filters}
        onChange={setFilters}
        paused={paused}
        onPause={pause}
        onResume={resume}
        onRefresh={handleRefresh}
      />

      {liveCount >= LIVE_BUFFER_MAX && (
        <div className="flex items-center gap-2 border-b border-white/5 bg-tg-orange/10 px-3 py-1.5 text-xs text-tg-orange">
          <TriangleAlert size={14} />
          Showing the newest {LIVE_BUFFER_MAX} live records; older ones scrolled
          out of memory. Reload to read them from history.
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Spinner />
          </div>
        ) : isError ? (
          <EmptyState
            icon={TriangleAlert}
            title="Could not load logs"
            description="The log store did not answer. Check that Loki is running, then retry."
            className="py-24"
          />
        ) : records.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No logs yet"
            description="Logs appear here once the bot ships them with the steeper library's log capture enabled."
            className="py-24"
          />
        ) : (
          <>
            {records.map((record) => (
              <LogRow
                key={`${record.cursor}:${record.message}`}
                record={record}
              />
            ))}

            {hasNextPage && (
              <div className="flex justify-center py-4">
                <button
                  type="button"
                  onClick={() => void fetchNextPage()}
                  disabled={isFetchingNextPage}
                  className="rounded-lg bg-white/5 px-4 py-2 text-xs text-tg-text-secondary transition-colors hover:bg-white/10 hover:text-tg-text disabled:opacity-50"
                >
                  {isFetchingNextPage ? "Loading…" : "Load older"}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
