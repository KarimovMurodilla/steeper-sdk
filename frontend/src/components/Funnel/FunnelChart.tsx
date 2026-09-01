import { useElementWidth } from "@/hooks/useElementWidth";
import { formatDuration, formatPercent, truncate } from "@/lib/utils";
import type { FunnelStepReport } from "@/types/api";

interface Props {
  steps: FunnelStepReport[];
  totalEntered: number;
}

const BAND_HEIGHT = 46;
const GAP_HEIGHT = 34;
/**
 * A step nobody reached still gets a sliver of width. A bar of literal zero
 * width reads as a rendering bug; a hairline reads as "measured, and it is
 * zero", which is what the data says.
 */
const MIN_BAND_WIDTH = 6;
/** Roughly the advance width of the 11px label font, for truncation. */
const LABEL_CHAR_WIDTH = 6.2;

/**
 * One hue for every band. The bands differ in size, not in kind, and a
 * categorical palette here would imply a distinction between steps that does
 * not exist — the shrinking width is the whole message.
 */
const BAND_COLOR = "rgb(var(--tg-primary))";

/**
 * The funnel itself: one band per step, width proportional to the users who
 * reached it, joined by trapezoids so the drop-off is the visible shape rather
 * than something you have to compute from two numbers.
 */
export function FunnelChart({ steps, totalEntered }: Props) {
  const [ref, width] = useElementWidth<HTMLDivElement>();

  const height = steps.length * BAND_HEIGHT + (steps.length - 1) * GAP_HEIGHT;

  // Step names live in a gutter rather than on the bands: the last bands are
  // narrow by construction, so a name inside them would not fit exactly when
  // the funnel is most interesting.
  const gutter = Math.min(160, Math.max(80, width * 0.22));
  const plotWidth = Math.max(1, width - gutter);
  const centerX = gutter + plotWidth / 2;

  // Everything is measured against the funnel's entrants, so the first band is
  // always full width and each later one is read directly as a share of it.
  const scale = Math.max(1, totalEntered);
  const maxLabelChars = Math.floor((gutter - 12) / LABEL_CHAR_WIDTH);

  const bandWidth = (users: number) =>
    Math.max(MIN_BAND_WIDTH, (users / scale) * plotWidth);

  return (
    <div ref={ref} className="w-full">
      {width > 0 && (
        <svg width={width} height={height}>
          {steps.map((step, i) => {
            const w = bandWidth(step.users);
            const x = centerX - w / 2;
            const y = i * (BAND_HEIGHT + GAP_HEIGHT);
            const next = steps[i + 1];
            const nextWidth = next ? bandWidth(next.users) : 0;

            return (
              <g key={`${step.name}-${step.position}`}>
                {next && (
                  <polygon
                    points={[
                      `${x},${y + BAND_HEIGHT}`,
                      `${x + w},${y + BAND_HEIGHT}`,
                      `${centerX + nextWidth / 2},${y + BAND_HEIGHT + GAP_HEIGHT}`,
                      `${centerX - nextWidth / 2},${y + BAND_HEIGHT + GAP_HEIGHT}`,
                    ].join(" ")}
                    fill={BAND_COLOR}
                    opacity={0.1}
                  />
                )}

                <text
                  x={0}
                  y={y + BAND_HEIGHT / 2}
                  dominantBaseline="central"
                  className="fill-tg-text-secondary text-[11px]"
                >
                  <title>{step.name}</title>
                  {truncate(step.name, maxLabelChars)}
                </text>

                <rect
                  x={x}
                  y={y}
                  width={w}
                  height={BAND_HEIGHT}
                  rx={6}
                  fill={BAND_COLOR}
                  opacity={0.85}
                />

                <text
                  x={centerX}
                  y={y + BAND_HEIGHT / 2}
                  textAnchor="middle"
                  dominantBaseline="central"
                  className="fill-white text-[13px] font-semibold"
                >
                  {step.users.toLocaleString()}
                </text>

                {next && (
                  <text
                    x={centerX}
                    y={y + BAND_HEIGHT + GAP_HEIGHT / 2}
                    textAnchor="middle"
                    dominantBaseline="central"
                    className="fill-tg-text-muted text-[11px]"
                  >
                    {formatPercent(next.conversion_from_previous)}
                    {next.median_seconds_from_previous !== null &&
                      ` · ${formatDuration(next.median_seconds_from_previous)}`}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      )}
    </div>
  );
}
