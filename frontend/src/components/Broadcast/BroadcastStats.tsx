import { useState } from "react";
import { GlassCard } from "@/components/ui/GlassCard";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useBroadcastStats } from "@/hooks/useBroadcasts";
import { Spinner } from "@/components/ui/Spinner";

export function BroadcastStats() {
  const [id, setId] = useState("");
  const [trackId, setTrackId] = useState<string | null>(null);

  const { data, isLoading } = useBroadcastStats(trackId, true);

  return (
    <GlassCard className="p-6 max-w-xl">
      <h3 className="text-lg font-semibold mb-4">Broadcast Statistics</h3>
      <div className="flex gap-2 mb-6">
        <Input
          placeholder="Enter broadcast ID"
          value={id}
          onChange={(e) => setId(e.target.value)}
          className="flex-1"
        />
        <Button onClick={() => setTrackId(id || null)}>Track</Button>
      </div>

      {isLoading && trackId && (
        <div className="flex justify-center py-4">
          <Spinner />
        </div>
      )}

      {data && (
        <div className="grid grid-cols-3 gap-4">
          <StatBox label="Total" value={data.total} color="text-tg-accent" />
          <StatBox label="Sent" value={data.sent} color="text-tg-green" />
          <StatBox label="Failed" value={data.failed} color="text-tg-red" />
        </div>
      )}
    </GlassCard>
  );
}

function StatBox({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/5 p-4 text-center">
      <p className={`text-2xl font-bold ${color}`}>
        {value.toLocaleString()}
      </p>
      <p className="text-xs text-tg-text-muted mt-1">{label}</p>
    </div>
  );
}
