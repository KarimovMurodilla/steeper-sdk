import { Bot } from "lucide-react";
import { useActiveBot } from "@/hooks/useActiveBot";
import { LogViewer } from "@/components/Logs/LogViewer";
import { EmptyState } from "@/components/ui/EmptyState";

export function LogsPage() {
  const { activeBotId, bots, isLoading } = useActiveBot();

  if (!isLoading && bots.length === 0) {
    return (
      <EmptyState
        icon={Bot}
        title="No bots connected"
        description="Add a bot from the switcher to see its system logs."
        className="py-24"
      />
    );
  }

  return <LogViewer botId={activeBotId} />;
}
