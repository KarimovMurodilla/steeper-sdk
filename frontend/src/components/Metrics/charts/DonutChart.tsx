import { humanizeLabel } from "@/lib/utils";
import type { LabeledCount } from "@/types/api";
import { colorAt } from "./palette";

interface Props {
  data: LabeledCount[];
  size?: number;
}

export function DonutChart({ data, size = 160 }: Props) {
  const total = data.reduce((acc, d) => acc + d.count, 0);
  const radius = size / 2;
  const stroke = size * 0.16;
  const r = radius - stroke / 2;
  const circumference = 2 * Math.PI * r;

  let offset = 0;
  const segments = data.map((d, i) => {
    const fraction = total > 0 ? d.count / total : 0;
    const seg = {
      color: colorAt(i),
      dash: fraction * circumference,
      gap: circumference - fraction * circumference,
      rotation: (offset / circumference) * 360,
      label: d.label,
      count: d.count,
      pct: total > 0 ? Math.round(fraction * 100) : 0,
    };
    offset += fraction * circumference;
    return seg;
  });

  return (
    <div className="flex flex-col items-center gap-5 sm:flex-row sm:items-center sm:gap-6">
      <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={radius}
            cy={radius}
            r={r}
            fill="none"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth={stroke}
          />
          {total > 0 &&
            segments.map((s, i) => (
              <circle
                key={i}
                cx={radius}
                cy={radius}
                r={r}
                fill="none"
                stroke={s.color}
                strokeWidth={stroke}
                strokeDasharray={`${s.dash} ${s.gap}`}
                strokeDashoffset={-s.rotation * (circumference / 360)}
                strokeLinecap="butt"
              />
            ))}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-tg-text">
            {total.toLocaleString()}
          </span>
          <span className="text-[11px] text-tg-text-muted">total</span>
        </div>
      </div>

      <div className="flex-1 space-y-2">
        {segments.map((s, i) => (
          <div key={i} className="flex items-center gap-2 text-sm">
            <span
              className="h-2.5 w-2.5 flex-shrink-0 rounded-full"
              style={{ backgroundColor: s.color }}
            />
            <span className="flex-1 truncate text-tg-text-secondary">
              {humanizeLabel(s.label)}
            </span>
            <span className="font-medium text-tg-text">
              {s.count.toLocaleString()}
            </span>
            <span className="w-9 text-right text-xs text-tg-text-muted">
              {s.pct}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
