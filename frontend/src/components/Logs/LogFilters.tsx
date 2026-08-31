import { useEffect, useState } from "react";
import { Pause, Play, RotateCw, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LogFilters as Filters } from "@/hooks/useLogs";
import type { LogLevel } from "@/types/api";

const LEVELS: LogLevel[] = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"];

const levelActive: Record<LogLevel, string> = {
  DEBUG: "bg-white/10 text-tg-text",
  INFO: "bg-tg-primary/25 text-tg-accent",
  WARNING: "bg-tg-orange/25 text-tg-orange",
  ERROR: "bg-tg-red/25 text-tg-red",
  CRITICAL: "bg-tg-red/60 text-white",
};

// Typing in the search box changes the query key, so every keystroke would
// otherwise fire a request against the log store.
const SEARCH_DEBOUNCE_MS = 400;

interface Props {
  filters: Filters;
  onChange: (filters: Filters) => void;
  paused: boolean;
  onPause: () => void;
  onResume: () => void;
  onRefresh: () => void;
}

export function LogFilters({
  filters,
  onChange,
  paused,
  onPause,
  onResume,
  onRefresh,
}: Props) {
  const [search, setSearch] = useState(filters.search);
  const [loggerName, setLoggerName] = useState(filters.loggerName);

  useEffect(() => {
    const id = setTimeout(() => {
      if (search !== filters.search || loggerName !== filters.loggerName) {
        onChange({ ...filters, search, loggerName });
      }
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [search, loggerName, filters, onChange]);

  const toggleLevel = (level: LogLevel) => {
    const levels = filters.levels.includes(level)
      ? filters.levels.filter((l) => l !== level)
      : [...filters.levels, level];
    onChange({ ...filters, levels });
  };

  return (
    <div className="flex flex-wrap items-center gap-2 border-b border-white/5 bg-tg-bg-secondary/80 px-3 py-2 backdrop-blur-[20px]">
      <div className="flex items-center gap-1">
        {LEVELS.map((level) => {
          const active = filters.levels.includes(level);
          return (
            <button
              key={level}
              type="button"
              onClick={() => toggleLevel(level)}
              className={cn(
                "rounded-md px-2 py-1 font-mono text-[11px] font-semibold transition-colors",
                active
                  ? levelActive[level]
                  : "text-tg-text-muted hover:bg-white/5 hover:text-tg-text-secondary",
              )}
              aria-pressed={active}
            >
              {level}
            </button>
          );
        })}
      </div>

      <div className="relative min-w-[10rem] flex-1">
        <Search
          size={14}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-tg-text-muted"
        />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search message (case-sensitive)"
          className="w-full rounded-lg border border-white/10 bg-white/5 py-1.5 pl-8 pr-3 text-sm text-tg-text placeholder:text-tg-text-muted outline-none transition-colors focus:border-tg-primary"
        />
      </div>

      <input
        value={loggerName}
        onChange={(e) => setLoggerName(e.target.value)}
        placeholder="Logger prefix"
        className="w-40 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 font-mono text-xs text-tg-text placeholder:text-tg-text-muted outline-none transition-colors focus:border-tg-primary"
      />

      <button
        type="button"
        onClick={paused ? onResume : onPause}
        title={paused ? "Resume live tail" : "Pause live tail"}
        className={cn(
          "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
          paused
            ? "bg-tg-orange/20 text-tg-orange hover:bg-tg-orange/30"
            : "bg-white/5 text-tg-text-secondary hover:bg-white/10",
        )}
      >
        {paused ? <Play size={14} /> : <Pause size={14} />}
        {paused ? "Paused" : "Live"}
      </button>

      <button
        type="button"
        onClick={onRefresh}
        title="Reload history"
        className="rounded-lg bg-white/5 p-1.5 text-tg-text-secondary transition-colors hover:bg-white/10 hover:text-tg-text"
      >
        <RotateCw size={14} />
      </button>
    </div>
  );
}
