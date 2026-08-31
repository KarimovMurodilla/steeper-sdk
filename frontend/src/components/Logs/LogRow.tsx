import { useState } from "react";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { BotLogViewModel, LogLevel } from "@/types/api";

const levelStyles: Record<LogLevel, string> = {
  DEBUG: "text-tg-text-muted",
  INFO: "text-tg-accent",
  WARNING: "text-tg-orange",
  ERROR: "text-tg-red",
  CRITICAL: "text-white bg-tg-red/80 px-1 rounded",
};

/** Full timestamp with milliseconds — ordering matters more than prettiness here. */
function formatLogTime(iso: string): string {
  const d = new Date(iso);
  const time = d.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
  return `${time}.${String(d.getMilliseconds()).padStart(3, "0")}`;
}

interface Props {
  record: BotLogViewModel;
}

export function LogRow({ record }: Props) {
  const [expanded, setExpanded] = useState(false);
  const hasDetails =
    !!record.exc || Object.keys(record.extra ?? {}).length > 0 || !!record.module;

  return (
    <div
      className={cn(
        "border-b border-white/5 font-mono text-xs leading-relaxed hover:bg-white/[0.03]",
        record.level === "ERROR" || record.level === "CRITICAL"
          ? "bg-tg-red/5"
          : undefined,
      )}
    >
      <button
        type="button"
        onClick={() => hasDetails && setExpanded((v) => !v)}
        className={cn(
          "flex w-full items-start gap-3 px-3 py-1.5 text-left",
          hasDetails ? "cursor-pointer" : "cursor-default",
        )}
      >
        <ChevronRight
          size={12}
          className={cn(
            "mt-1 shrink-0 transition-transform",
            hasDetails ? "text-tg-text-muted" : "invisible",
            expanded && "rotate-90",
          )}
        />
        <time
          className="shrink-0 text-tg-text-muted"
          dateTime={record.ts}
          title={new Date(record.ts).toLocaleString()}
        >
          {formatLogTime(record.ts)}
        </time>
        <span
          className={cn("w-16 shrink-0 font-semibold", levelStyles[record.level])}
        >
          {record.level}
        </span>
        <span
          className="hidden w-56 shrink-0 truncate text-tg-text-secondary sm:block"
          title={record.logger}
        >
          {record.logger}
        </span>
        <span className="min-w-0 flex-1 whitespace-pre-wrap break-words text-tg-text">
          {record.message}
        </span>
      </button>

      {expanded && (
        <div className="space-y-2 border-t border-white/5 bg-black/20 px-3 py-2 pl-8">
          <div className="text-tg-text-muted">
            {record.logger}
            {record.module && ` · ${record.module}`}
            {record.func && ` · ${record.func}()`}
            {record.line !== null && `:${record.line}`}
          </div>
          {record.exc && (
            <pre className="overflow-x-auto whitespace-pre text-tg-red/90">
              {record.exc}
            </pre>
          )}
          {Object.keys(record.extra ?? {}).length > 0 && (
            <pre className="overflow-x-auto whitespace-pre-wrap text-tg-text-secondary">
              {JSON.stringify(record.extra, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
