/** Theme-aligned categorical colors for charts (cycled by index). */
export const CHART_COLORS = [
  "#5288c1", // tg primary blue
  "#64b5ef", // tg accent
  "#4fae4e", // green
  "#f5a623", // orange
  "#e2606b", // red/coral
  "#a78bfa", // violet
  "#22d3ee", // cyan
  "#f472b6", // pink
  "#34d399", // emerald
  "#fbbf24", // amber
];

export function colorAt(index: number): string {
  return CHART_COLORS[index % CHART_COLORS.length]!;
}
