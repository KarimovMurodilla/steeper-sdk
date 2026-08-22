import { useMemo } from "react";
import type { HeatmapCell } from "@/types/api";

interface Props {
  data: HeatmapCell[];
}

/** PostgreSQL `dow` order: 0 is Sunday. */
const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const HOURS = Array.from({ length: 24 }, (_, hour) => hour);

/** Update volume per weekday and hour of day, in UTC. */
export function Heatmap({ data }: Props) {
  const { counts, max } = useMemo(() => {
    const counts = new Map<string, number>();
    let max = 0;
    for (const cell of data) {
      counts.set(`${cell.weekday}-${cell.hour}`, cell.count);
      if (cell.count > max) max = cell.count;
    }
    return { counts, max };
  }, [data]);

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[560px]">
        <div className="flex">
          <div className="w-10 flex-shrink-0" />
          <div className="grid flex-1 gap-0.5"
            style={{ gridTemplateColumns: "repeat(24, minmax(0, 1fr))" }}>
            {HOURS.map((hour) => (
              <div
                key={hour}
                className="text-center text-[9px] leading-4 text-tg-text-muted"
              >
                {hour % 3 === 0 ? hour : ""}
              </div>
            ))}
          </div>
        </div>

        {WEEKDAYS.map((name, weekday) => (
          <div key={name} className="flex items-center">
            <div className="w-10 flex-shrink-0 pr-2 text-right text-[10px] text-tg-text-muted">
              {name}
            </div>
            <div className="grid flex-1 gap-0.5 py-0.5"
              style={{ gridTemplateColumns: "repeat(24, minmax(0, 1fr))" }}>
              {HOURS.map((hour) => {
                const count = counts.get(`${weekday}-${hour}`) ?? 0;
                const intensity = max > 0 ? count / max : 0;
                return (
                  <div
                    key={hour}
                    title={`${name} ${String(hour).padStart(2, "0")}:00 UTC — ${count.toLocaleString()}`}
                    className="aspect-square rounded-[2px] bg-tg-accent transition-colors"
                    style={{ opacity: count === 0 ? 0.06 : 0.2 + intensity * 0.8 }}
                  />
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
