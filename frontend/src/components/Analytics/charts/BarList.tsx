import { humanizeLabel } from "@/lib/utils";
import type { LabeledCount } from "@/types/api";
import { colorAt } from "./palette";

interface Props {
  data: LabeledCount[];
}

export function BarList({ data }: Props) {
  const max = Math.max(1, ...data.map((d) => d.count));

  return (
    <div className="space-y-3">
      {data.map((d, i) => (
        <div key={d.label}>
          <div className="mb-1 flex items-center justify-between text-sm">
            <span className="truncate text-tg-text-secondary">
              {humanizeLabel(d.label)}
            </span>
            <span className="font-medium text-tg-text">
              {d.count.toLocaleString()}
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${(d.count / max) * 100}%`,
                backgroundColor: colorAt(i),
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
