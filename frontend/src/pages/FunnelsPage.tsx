import { useEffect, useState } from "react";
import { Filter, Plus } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Spinner } from "@/components/ui/Spinner";
import { FunnelFormModal } from "@/components/Funnel/FunnelFormModal";
import { FunnelList } from "@/components/Funnel/FunnelList";
import { FunnelReportView } from "@/components/Funnel/FunnelReportView";
import { useActiveBot } from "@/hooks/useActiveBot";
import { useFunnels } from "@/hooks/useFunnels";
import type { FunnelViewModel } from "@/types/api";

export function FunnelsPage() {
  const { activeBotId, bots, isLoading: botsLoading } = useActiveBot();
  const { data: funnels, isLoading } = useFunnels(activeBotId);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<FunnelViewModel | undefined>();

  // Keep a selection alive across refetches, and drop one that was deleted.
  useEffect(() => {
    if (!funnels) return;
    if (funnels.length === 0) {
      setSelectedId(null);
      return;
    }
    if (!funnels.some((funnel) => funnel.id === selectedId)) {
      setSelectedId(funnels[0]!.id);
    }
  }, [funnels, selectedId]);

  // A funnel belongs to one bot, so a switch invalidates the whole view.
  useEffect(() => {
    setSelectedId(null);
  }, [activeBotId]);

  const selected = funnels?.find((funnel) => funnel.id === selectedId);

  const openCreate = () => {
    setEditing(undefined);
    setFormOpen(true);
  };

  const openEdit = (funnel: FunnelViewModel) => {
    setEditing(funnel);
    setFormOpen(true);
  };

  return (
    <div className="mx-auto max-w-5xl p-4 sm:p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Funnels</h1>
          <p className="mt-1 text-sm text-tg-text-muted">
            Where users drop off between the events your bot reports.
          </p>
        </div>
        {activeBotId && (
          <Button onClick={openCreate}>
            <Plus size={16} />
            New funnel
          </Button>
        )}
      </div>

      {!botsLoading && bots.length === 0 && (
        <EmptyState
          icon={Filter}
          title="No bots yet"
          description="Add a bot from the sidebar to start tracking funnels."
        />
      )}

      {activeBotId && isLoading && (
        <div className="flex h-60 items-center justify-center">
          <Spinner size="lg" />
        </div>
      )}

      {activeBotId && !isLoading && funnels?.length === 0 && (
        <EmptyState
          icon={Filter}
          title="No funnels yet"
          description="A funnel is an ordered list of events plus a conversion window. Create one to see how many users make it from the first step to the last."
          action={
            <Button onClick={openCreate}>
              <Plus size={16} />
              New funnel
            </Button>
          }
        />
      )}

      {activeBotId && funnels && funnels.length > 0 && (
        <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
          <FunnelList
            botId={activeBotId}
            funnels={funnels}
            selectedId={selectedId}
            onSelect={(funnel) => setSelectedId(funnel.id)}
            onEdit={openEdit}
          />
          {selected && (
            <FunnelReportView botId={activeBotId} funnel={selected} />
          )}
        </div>
      )}

      {activeBotId && (
        <FunnelFormModal
          botId={activeBotId}
          open={formOpen}
          onClose={() => setFormOpen(false)}
          funnel={editing}
        />
      )}
    </div>
  );
}
