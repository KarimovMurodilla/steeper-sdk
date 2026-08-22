import { useMemo, useState } from "react";
import { useElementWidth } from "@/hooks/useElementWidth";
import { formatCompact } from "@/lib/utils";
import type { TimeBucketCount, TimeGranularity } from "@/types/api";

interface Props {
  data: TimeBucketCount[];
  granularity: TimeGranularity;
  height?: number;
  color?: string;
}

function axisLabel(iso: string, g: TimeGranularity): string {
  const d = new Date(iso);
  if (g === "hour")
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (g === "month") return d.toLocaleDateString([], { month: "short" });
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

function tooltipLabel(iso: string, g: TimeGranularity): string {
  const d = new Date(iso);
  if (g === "hour")
    return d.toLocaleString([], {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  if (g === "month")
    return d.toLocaleDateString([], { month: "long", year: "numeric" });
  return d.toLocaleDateString([], {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

/** Build a smooth (cardinal-spline) SVG path through the given points. */
function smoothPath(pts: { x: number; y: number }[]): string {
  if (pts.length === 0) return "";
  if (pts.length === 1) return `M ${pts[0]!.x} ${pts[0]!.y}`;
  const t = 0.2;
  let d = `M ${pts[0]!.x} ${pts[0]!.y}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] ?? pts[i]!;
    const p1 = pts[i]!;
    const p2 = pts[i + 1]!;
    const p3 = pts[i + 2] ?? p2;
    const c1x = p1.x + (p2.x - p0.x) * t;
    const c1y = p1.y + (p2.y - p0.y) * t;
    const c2x = p2.x - (p3.x - p1.x) * t;
    const c2y = p2.y - (p3.y - p1.y) * t;
    d += ` C ${c1x} ${c1y}, ${c2x} ${c2y}, ${p2.x} ${p2.y}`;
  }
  return d;
}

export function AreaChart({
  data,
  granularity,
  height = 240,
  color = "#5288c1",
}: Props) {
  const [ref, width] = useElementWidth<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);

  const pad = { top: 16, right: 16, bottom: 26, left: 36 };
  const innerW = Math.max(0, width - pad.left - pad.right);
  const innerH = height - pad.top - pad.bottom;
  const max = Math.max(1, ...data.map((d) => d.count));

  const points = useMemo(() => {
    if (data.length === 0 || innerW <= 0) return [];
    const step = data.length > 1 ? innerW / (data.length - 1) : 0;
    return data.map((d, i) => ({
      x: pad.left + (data.length > 1 ? i * step : innerW / 2),
      y: pad.top + innerH - (d.count / max) * innerH,
      datum: d,
    }));
  }, [data, innerW, innerH, max, pad.left, pad.top]);

  const line = smoothPath(points);
  const area =
    points.length > 0
      ? `${line} L ${points[points.length - 1]!.x} ${pad.top + innerH} L ${
          points[0]!.x
        } ${pad.top + innerH} Z`
      : "";

  const gridLines = [0, 0.25, 0.5, 0.75, 1];
  const gradId = "areaGrad";

  const handleMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (points.length === 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    let nearest = 0;
    let best = Infinity;
    points.forEach((p, i) => {
      const dist = Math.abs(p.x - x);
      if (dist < best) {
        best = dist;
        nearest = i;
      }
    });
    setHover(nearest);
  };

  const hoverPoint = hover != null ? points[hover] : null;

  return (
    <div ref={ref} className="relative w-full" style={{ height }}>
      {width > 0 && (
        <svg
          width={width}
          height={height}
          onMouseMove={handleMove}
          onMouseLeave={() => setHover(null)}
          className="overflow-visible"
        >
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.35} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>

          {/* grid + y labels */}
          {gridLines.map((g) => {
            const y = pad.top + innerH * g;
            const value = Math.round(max * (1 - g));
            return (
              <g key={g}>
                <line
                  x1={pad.left}
                  y1={y}
                  x2={width - pad.right}
                  y2={y}
                  stroke="rgba(255,255,255,0.06)"
                  strokeWidth={1}
                />
                <text
                  x={pad.left - 8}
                  y={y + 3}
                  textAnchor="end"
                  className="fill-tg-text-muted"
                  fontSize={10}
                >
                  {formatCompact(value)}
                </text>
              </g>
            );
          })}

          {area && <path d={area} fill={`url(#${gradId})`} />}
          {line && (
            <path
              d={line}
              fill="none"
              stroke={color}
              strokeWidth={2}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          )}

          {/* x labels */}
          {points.length > 0 &&
            [0, Math.floor(points.length / 2), points.length - 1]
              .filter((v, i, a) => a.indexOf(v) === i)
              .map((i) => (
                <text
                  key={i}
                  x={points[i]!.x}
                  y={height - 8}
                  textAnchor={
                    i === 0
                      ? "start"
                      : i === points.length - 1
                        ? "end"
                        : "middle"
                  }
                  className="fill-tg-text-muted"
                  fontSize={10}
                >
                  {axisLabel(points[i]!.datum.bucket, granularity)}
                </text>
              ))}

          {/* hover guide */}
          {hoverPoint && (
            <>
              <line
                x1={hoverPoint.x}
                y1={pad.top}
                x2={hoverPoint.x}
                y2={pad.top + innerH}
                stroke="rgba(255,255,255,0.2)"
                strokeWidth={1}
              />
              <circle
                cx={hoverPoint.x}
                cy={hoverPoint.y}
                r={4}
                fill={color}
                stroke="#0e1621"
                strokeWidth={2}
              />
            </>
          )}
        </svg>
      )}

      {hoverPoint && (
        <div
          className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-lg border border-white/10 bg-tg-bg/95 px-2.5 py-1.5 text-center shadow-xl backdrop-blur-[20px]"
          style={{
            left: Math.min(Math.max(hoverPoint.x, 60), width - 60),
            top: hoverPoint.y - 8,
          }}
        >
          <p className="text-sm font-semibold text-tg-text">
            {hoverPoint.datum.count.toLocaleString()}
          </p>
          <p className="whitespace-nowrap text-[11px] text-tg-text-muted">
            {tooltipLabel(hoverPoint.datum.bucket, granularity)}
          </p>
        </div>
      )}
    </div>
  );
}
