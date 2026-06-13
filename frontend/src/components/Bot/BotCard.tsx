import { MoreVertical, Trash2, Pencil, Power } from "lucide-react";
import { useState } from "react";
import type { BotViewModel } from "@/types/api";
import { GlassCard } from "@/components/ui/GlassCard";
import { Badge } from "@/components/ui/Badge";
import { formatDate } from "@/lib/utils";

const statusVariant = {
  active: "success" as const,
  disabled: "danger" as const,
  maintenance: "warning" as const,
};

interface Props {
  bot: BotViewModel;
  onSelect: (id: string) => void;
  onEdit: (bot: BotViewModel) => void;
  onDelete: (id: string) => void;
  onToggle: (bot: BotViewModel) => void;
}

export function BotCard({ bot, onSelect, onEdit, onDelete, onToggle }: Props) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <GlassCard className="p-4 animate-fade-in">
      <div className="flex items-start justify-between">
        <button
          onClick={() => onSelect(bot.id)}
          className="flex-1 text-left"
        >
          <h3 className="font-semibold text-tg-text">{bot.name}</h3>
          <p className="text-xs text-tg-text-muted mt-1">
            Created {formatDate(bot.created_at)}
          </p>
        </button>

        <div className="flex items-center gap-2">
          <Badge variant={statusVariant[bot.status]}>{bot.status}</Badge>
          <div className="relative">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="rounded-lg p-1.5 text-tg-text-muted hover:bg-white/10 transition-colors"
            >
              <MoreVertical size={16} />
            </button>
            {menuOpen && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setMenuOpen(false)}
                />
                <div className="absolute right-0 top-8 z-20 min-w-[160px] rounded-xl border border-white/10 bg-tg-bg/95 backdrop-blur-[20px] shadow-xl py-1 animate-fade-in">
                  <button
                    onClick={() => {
                      onToggle(bot);
                      setMenuOpen(false);
                    }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-tg-text-secondary hover:bg-white/5"
                  >
                    <Power size={14} />
                    {bot.status === "active" ? "Disable" : "Enable"}
                  </button>
                  <button
                    onClick={() => {
                      onEdit(bot);
                      setMenuOpen(false);
                    }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-tg-text-secondary hover:bg-white/5"
                  >
                    <Pencil size={14} />
                    Edit Token
                  </button>
                  <button
                    onClick={() => {
                      onDelete(bot.id);
                      setMenuOpen(false);
                    }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-tg-red hover:bg-white/5"
                  >
                    <Trash2 size={14} />
                    Delete
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </GlassCard>
  );
}
