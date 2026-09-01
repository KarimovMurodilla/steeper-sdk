import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BarChart3,
  Bot as BotIcon,
  Filter,
  Megaphone,
  MessageSquare,
  ScrollText,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";
import { useBots } from "@/hooks/useBots";

interface Command {
  id: string;
  label: string;
  hint?: string;
  icon: LucideIcon;
  group: "Go to" | "Switch bot";
  run: () => void;
}

const ROUTES: { to: string; label: string; icon: LucideIcon }[] = [
  { to: "/chats", label: "Chats", icon: MessageSquare },
  { to: "/broadcasts", label: "Broadcasts", icon: Megaphone },
  { to: "/metrics", label: "Analytics", icon: BarChart3 },
  { to: "/funnels", label: "Funnels", icon: Filter },
  { to: "/logs", label: "Logs", icon: ScrollText },
];

/**
 * Ctrl/Cmd+K launcher for navigation and bot switching — the two things that
 * otherwise cost a trip to the sidebar on every task.
 */
export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen, activeBotId } =
    useUIStore();
  const setActiveBotId = useUIStore((state) => state.setActiveBotId);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState(0);

  // Only fetched while the palette is open, so it costs nothing otherwise.
  const { data: botsData } = useBots(1, 100);

  const close = useCallback(() => {
    setCommandPaletteOpen(false);
    setQuery("");
    setCursor(0);
  }, [setCommandPaletteOpen]);

  const commands = useMemo<Command[]>(() => {
    const routes: Command[] = ROUTES.map((route) => ({
      id: `route:${route.to}`,
      label: route.label,
      icon: route.icon,
      group: "Go to",
      run: () => navigate(route.to),
    }));

    const bots: Command[] = (botsData?.items ?? []).map((bot) => ({
      id: `bot:${bot.id}`,
      label: bot.name,
      hint: bot.id === activeBotId ? "Active" : undefined,
      icon: BotIcon,
      group: "Switch bot",
      run: () => setActiveBotId(bot.id),
    }));

    return [...routes, ...bots];
  }, [botsData, activeBotId, navigate, setActiveBotId]);

  const results = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return commands;
    return commands.filter((c) =>
      `${c.label} ${c.group}`.toLowerCase().includes(needle),
    );
  }, [commands, query]);

  // Global hotkey: Ctrl+K / Cmd+K toggles the palette from anywhere.
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandPaletteOpen(!useUIStore.getState().commandPaletteOpen);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [setCommandPaletteOpen]);

  useEffect(() => {
    if (commandPaletteOpen) inputRef.current?.focus();
  }, [commandPaletteOpen]);

  useEffect(() => {
    setCursor(0);
  }, [query]);

  // Keep the highlighted row inside the scroll viewport.
  useEffect(() => {
    listRef.current
      ?.querySelector<HTMLElement>(`[data-index="${cursor}"]`)
      ?.scrollIntoView({ block: "nearest" });
  }, [cursor]);

  if (!commandPaletteOpen) return null;

  const runAt = (index: number) => {
    const command = results[index];
    if (!command) return;
    command.run();
    close();
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault();
      close();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setCursor((c) => (results.length ? (c + 1) % results.length : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setCursor((c) =>
        results.length ? (c - 1 + results.length) % results.length : 0,
      );
    } else if (e.key === "Enter") {
      e.preventDefault();
      runAt(cursor);
    }
  };

  let lastGroup: Command["group"] | null = null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-[12vh]">
      <div className="absolute inset-0 bg-black/60" onClick={close} />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        onKeyDown={onKeyDown}
        className="relative w-full max-w-lg overflow-hidden rounded-2xl border border-tg-overlay/10 bg-tg-bg/95 shadow-2xl backdrop-blur-[20px] animate-fade-in"
      >
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search pages and bots…"
          aria-label="Command"
          className="w-full border-b border-tg-overlay/5 bg-transparent px-5 py-4 text-sm text-tg-text outline-none placeholder:text-tg-text-muted"
        />

        <div ref={listRef} className="max-h-80 overflow-y-auto py-2">
          {results.length === 0 ? (
            <p className="px-5 py-6 text-center text-sm text-tg-text-muted">
              Nothing matches “{query.trim()}”.
            </p>
          ) : (
            results.map((command, index) => {
              const Icon = command.icon;
              const groupChanged = command.group !== lastGroup;
              lastGroup = command.group;

              return (
                <div key={command.id}>
                  {groupChanged && (
                    <p className="px-5 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wide text-tg-text-muted">
                      {command.group}
                    </p>
                  )}
                  <button
                    data-index={index}
                    onMouseEnter={() => setCursor(index)}
                    onClick={() => runAt(index)}
                    className={cn(
                      "flex w-full items-center gap-3 px-5 py-2.5 text-left text-sm transition-colors",
                      index === cursor
                        ? "bg-tg-primary/15 text-tg-accent"
                        : "text-tg-text hover:bg-tg-overlay/5",
                    )}
                  >
                    <Icon size={16} className="flex-shrink-0" />
                    <span className="flex-1 truncate">{command.label}</span>
                    {command.hint && (
                      <span className="text-xs text-tg-text-muted">
                        {command.hint}
                      </span>
                    )}
                  </button>
                </div>
              );
            })
          )}
        </div>

        <div className="flex items-center gap-3 border-t border-tg-overlay/5 px-5 py-2 text-[11px] text-tg-text-muted">
          <span>↑↓ navigate</span>
          <span>↵ select</span>
          <span>esc close</span>
        </div>
      </div>
    </div>
  );
}
