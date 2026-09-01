import { Monitor, Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";
import { useThemeStore, type ThemePreference } from "@/store/themeStore";

const OPTIONS: { value: ThemePreference; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
];

export function ThemeToggle() {
  const { preference, setPreference } = useThemeStore();

  return (
    <div
      role="radiogroup"
      aria-label="Colour theme"
      className="flex rounded-lg border border-tg-overlay/10 bg-tg-overlay/5 p-0.5"
    >
      {OPTIONS.map(({ value, label, icon: Icon }) => (
        <button
          key={value}
          role="radio"
          aria-checked={preference === value}
          aria-label={label}
          title={label}
          onClick={() => setPreference(value)}
          className={cn(
            "flex flex-1 items-center justify-center rounded-md py-1.5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tg-accent",
            preference === value
              ? "bg-tg-primary/20 text-tg-accent"
              : "text-tg-text-muted hover:text-tg-text-secondary",
          )}
        >
          <Icon size={14} />
        </button>
      ))}
    </div>
  );
}
