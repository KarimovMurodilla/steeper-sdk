import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const dayMs = 86_400_000;

  if (diff < dayMs) return formatTime(iso);
  if (diff < 2 * dayMs) return "Yesterday";
  if (diff < 7 * dayMs) return d.toLocaleDateString([], { weekday: "short" });
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

export function displayName(
  firstName: string | null | undefined,
  lastName?: string | null,
  username?: string | null,
): string {
  const parts: string[] = [];
  if (firstName) parts.push(firstName);
  if (lastName) parts.push(lastName);
  if (parts.length > 0) return parts.join(" ");
  if (username) return `@${username}`;
  return "Unknown";
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export function truncate(str: string, max: number): string {
  if (str.length <= max) return str;
  return str.slice(0, max) + "…";
}

/** Compact number formatting: 1234 -> "1.2K", 2_500_000 -> "2.5M". */
export function formatCompact(n: number): string {
  if (n < 1000) return String(n);
  return new Intl.NumberFormat([], {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(n);
}

/** Turn an API enum label like "callback_query" into "Callback Query". */
export function humanizeLabel(label: string): string {
  return label
    .replace(/[_-]+/g, " ")
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Format a 0..1 ratio as a percentage.
 *
 * Null means "no data to divide by" — a funnel step nobody could convert from —
 * and must stay visually distinct from a real 0%, which is a measured outcome.
 */
export function formatPercent(ratio: number | null, digits = 1): string {
  if (ratio === null || !Number.isFinite(ratio)) return "—";
  return `${(ratio * 100).toFixed(digits)}%`;
}

/** Format a duration in seconds as a short human string: "2h 14m", "45s". */
export function formatDuration(seconds: number | null): string {
  if (seconds === null || !Number.isFinite(seconds)) return "—";
  if (seconds < 1) return "<1s";
  if (seconds < 60) return `${Math.round(seconds)}s`;

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    const rest = minutes % 60;
    return rest ? `${hours}h ${rest}m` : `${hours}h`;
  }

  const days = Math.floor(hours / 24);
  const rest = hours % 24;
  return rest ? `${days}d ${rest}h` : `${days}d`;
}
