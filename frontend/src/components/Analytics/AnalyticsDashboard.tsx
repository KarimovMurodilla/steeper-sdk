import { Users, MessageSquare, MessagesSquare, Activity } from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { Spinner } from "@/components/ui/Spinner";
import { useBotAnalytics } from "@/hooks/useAnalytics";
import type { LucideIcon } from "lucide-react";

interface Props {
  botId: string | null;
}

export function AnalyticsDashboard({ botId }: Props) {
  const { data, isLoading } = useBotAnalytics(botId);

  if (!botId) {
    return (
      <p className="text-tg-text-muted text-center py-16">
        Select a bot to view analytics
      </p>
    );
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!data) return null;

  const cards: { label: string; value: number; icon: LucideIcon; color: string }[] = [
    { label: "Users", value: data.users, icon: Users, color: "text-tg-accent" },
    {
      label: "Chats",
      value: data.chats,
      icon: MessageSquare,
      color: "text-tg-green",
    },
    {
      label: "Messages",
      value: data.messages,
      icon: MessagesSquare,
      color: "text-tg-orange",
    },
    { label: "DAU", value: data.dau, icon: Activity, color: "text-violet-400" },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(({ label, value, icon: Icon, color }) => (
        <GlassCard key={label} className="p-5">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 ${color}`}
            >
              <Icon size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold">{value.toLocaleString()}</p>
              <p className="text-xs text-tg-text-muted">{label}</p>
            </div>
          </div>
        </GlassCard>
      ))}
    </div>
  );
}
