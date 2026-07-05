import { useState } from "react";
import toast from "react-hot-toast";
import {
  Plus,
  ChevronDown,
  Power,
  Pencil,
  Trash2,
  Bot as BotIcon,
  Copy,
  Check,
} from "lucide-react";
import { useActiveBot } from "@/hooks/useActiveBot";
import { useUpdateBot, useDeleteBot } from "@/hooks/useBots";
import { useUIStore } from "@/store/uiStore";
import { cn } from "@/lib/utils";
import { Avatar } from "@/components/ui/Avatar";
import { AddBotModal } from "@/components/Bot/AddBotModal";
import { EditBotModal } from "@/components/Bot/EditBotModal";
import type { BotViewModel } from "@/types/api";

/**
 * Unified, global bot account switcher — modelled on Telegram's account
 * management sheet. Handles adding, selecting and managing every bot, so the
 * rest of the app simply operates on the active bot in the UI store.
 */
export function BotSwitcher() {
  const [open, setOpen] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [editBot, setEditBot] = useState<BotViewModel | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const { activeBotId, bots } = useActiveBot();
  const { setActiveBotId } = useUIStore();
  const updateBot = useUpdateBot();
  const deleteBot = useDeleteBot();

  const active = bots.find((b) => b.id === activeBotId) ?? null;

  const handleSelect = (id: string) => {
    setActiveBotId(id);
    setOpen(false);
  };

  const handleToggle = (bot: BotViewModel) => {
    updateBot.mutate({
      id: bot.id,
      data: { status: bot.status === "active" ? "disabled" : "active" },
    });
  };

  const handleCopyId = async (id: string) => {
    try {
      await navigator.clipboard.writeText(id);
      setCopiedId(id);
      toast.success("Bot ID copied");
      setTimeout(() => setCopiedId((c) => (c === id ? null : c)), 1500);
    } catch {
      toast.error("Failed to copy");
    }
  };

  const handleDelete = (bot: BotViewModel) => {
    if (!window.confirm(`Delete "${bot.name}"?`)) return;
    deleteBot.mutate(bot.id, {
      onSuccess: () => {
        if (bot.id === activeBotId) setActiveBotId(null);
      },
    });
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-left transition-colors hover:bg-white/10"
      >
        {active ? (
          <Avatar name={active.name} size="sm" className="h-9 w-9 text-sm" />
        ) : (
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-tg-text-muted">
            <BotIcon size={18} />
          </span>
        )}
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-tg-text">
            {active?.name ?? (bots.length ? "Select a bot" : "No bots yet")}
          </p>
          <p className="text-xs text-tg-text-muted">
            {active ? active.status : "Tap to add"}
          </p>
        </div>
        <ChevronDown
          size={16}
          className={cn(
            "shrink-0 text-tg-text-muted transition-transform",
            open && "rotate-180",
          )}
        />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-30" onClick={() => setOpen(false)} />
          <div className="absolute bottom-full left-0 z-40 mb-2 w-full overflow-hidden rounded-2xl border border-white/10 bg-tg-bg/95 py-1.5 shadow-2xl backdrop-blur-[20px] animate-fade-in">
            <button
              onClick={() => {
                setAddOpen(true);
                setOpen(false);
              }}
              className="flex w-full items-center gap-3 px-3 py-2.5 text-left text-sm font-medium text-tg-text transition-colors hover:bg-white/5"
            >
              <span className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-tg-text-secondary text-tg-text-secondary">
                <Plus size={18} />
              </span>
              Add Bot
            </button>

            {bots.length > 0 && <div className="my-1 h-px bg-white/10" />}

            <div className="max-h-72 overflow-y-auto">
              {bots.map((bot) => (
                <div
                  key={bot.id}
                  className={cn(
                    "group flex items-center gap-3 px-3 py-2 transition-colors hover:bg-white/5",
                    bot.id === activeBotId && "bg-white/5",
                  )}
                >
                  <button
                    onClick={() => handleSelect(bot.id)}
                    className="flex min-w-0 flex-1 items-center gap-3 text-left"
                  >
                    <Avatar
                      name={bot.name}
                      size="sm"
                      className={cn(
                        "h-9 w-9 text-sm",
                        bot.id === activeBotId && "ring-2 ring-tg-accent ring-offset-2 ring-offset-tg-bg",
                      )}
                    />
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-1.5">
                        <span className="truncate text-sm font-medium text-tg-text">
                          {bot.name}
                        </span>
                        {bot.status !== "active" && (
                          <span className="shrink-0 text-xs text-tg-text-muted">
                            · {bot.status}
                          </span>
                        )}
                      </span>
                      <span
                        role="button"
                        tabIndex={0}
                        title="Copy bot ID"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCopyId(bot.id);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            e.stopPropagation();
                            handleCopyId(bot.id);
                          }
                        }}
                        className="group/id mt-0.5 flex items-center gap-1 font-mono text-xs text-tg-text-muted transition-colors hover:text-tg-text-secondary"
                      >
                        <span className="truncate">{bot.id}</span>
                        {copiedId === bot.id ? (
                          <Check size={11} className="shrink-0 text-tg-green" />
                        ) : (
                          <Copy
                            size={11}
                            className="shrink-0 opacity-60 group-hover/id:opacity-100"
                          />
                        )}
                      </span>
                    </span>
                  </button>

                  <div className="flex shrink-0 items-center gap-0.5 opacity-60 transition-opacity group-hover:opacity-100">
                    <button
                      onClick={() => handleToggle(bot)}
                      title={bot.status === "active" ? "Disable" : "Enable"}
                      className="rounded-lg p-1.5 text-tg-text-muted hover:bg-white/10 hover:text-tg-text"
                    >
                      <Power size={14} />
                    </button>
                    <button
                      onClick={() => {
                        setEditBot(bot);
                        setOpen(false);
                      }}
                      title="Edit token"
                      className="rounded-lg p-1.5 text-tg-text-muted hover:bg-white/10 hover:text-tg-text"
                    >
                      <Pencil size={14} />
                    </button>
                    <button
                      onClick={() => handleDelete(bot)}
                      title="Delete"
                      className="rounded-lg p-1.5 text-tg-text-muted hover:bg-white/10 hover:text-tg-red"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      <AddBotModal open={addOpen} onClose={() => setAddOpen(false)} />
      <EditBotModal
        open={!!editBot}
        onClose={() => setEditBot(null)}
        bot={editBot}
      />
    </div>
  );
}
