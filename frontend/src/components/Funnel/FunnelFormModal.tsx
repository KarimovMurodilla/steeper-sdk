import { useEffect, useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { StepsEditor } from "./StepsEditor";
import {
  MAX_FUNNEL_STEPS,
  MAX_WINDOW_SECONDS,
  MIN_FUNNEL_STEPS,
  MIN_WINDOW_SECONDS,
  useCreateFunnel,
  useEventNames,
  useUpdateFunnel,
} from "@/hooks/useFunnels";
import type { FunnelViewModel } from "@/types/api";

interface Props {
  botId: string;
  open: boolean;
  onClose: () => void;
  /** Present when editing; absent when creating. */
  funnel?: FunnelViewModel;
}

/** Conversion-window presets, in seconds. */
const WINDOWS = [
  { label: "1 hour", value: 3_600 },
  { label: "1 day", value: 86_400 },
  { label: "7 days", value: 604_800 },
  { label: "30 days", value: 2_592_000 },
];

const EMPTY_STEPS = ["", ""];

export function FunnelFormModal({ botId, open, onClose, funnel }: Props) {
  const editing = funnel !== undefined;

  const [name, setName] = useState("");
  const [steps, setSteps] = useState<string[]>(EMPTY_STEPS);
  const [windowSeconds, setWindowSeconds] = useState(86_400);

  const { data: eventNames, isLoading: namesLoading } = useEventNames(
    open ? botId : null,
  );
  const create = useCreateFunnel(botId);
  const update = useUpdateFunnel(botId);
  const pending = create.isPending || update.isPending;

  // Reset on every open so a cancelled edit never leaks into the next one.
  useEffect(() => {
    if (!open) return;
    setName(funnel?.name ?? "");
    setSteps(funnel ? [...funnel.steps] : EMPTY_STEPS);
    setWindowSeconds(funnel?.window_seconds ?? 86_400);
  }, [open, funnel]);

  const trimmedSteps = steps.map((step) => step.trim());
  const valid =
    name.trim().length > 0 &&
    trimmedSteps.every((step) => step.length > 0) &&
    trimmedSteps.length >= MIN_FUNNEL_STEPS &&
    trimmedSteps.length <= MAX_FUNNEL_STEPS &&
    windowSeconds >= MIN_WINDOW_SECONDS &&
    windowSeconds <= MAX_WINDOW_SECONDS;

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!valid || pending) return;

    const payload = {
      name: name.trim(),
      steps: trimmedSteps,
      window_seconds: windowSeconds,
    };

    if (editing) {
      update.mutate(
        { funnelId: funnel.id, data: payload },
        { onSuccess: onClose },
      );
    } else {
      create.mutate(payload, { onSuccess: onClose });
    }
  };

  return (
    <Modal
      open={open}
      onClose={pending ? () => {} : onClose}
      title={editing ? "Edit funnel" : "New funnel"}
      className="max-w-lg"
    >
      <form onSubmit={submit} className="space-y-4">
        <Input
          label="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Onboarding to first payment"
          autoFocus
        />

        <StepsEditor
          steps={steps}
          onChange={setSteps}
          eventNames={eventNames ?? []}
          namesLoading={namesLoading}
        />

        <div className="space-y-1.5">
          <label className="block text-sm text-tg-text-secondary">
            Conversion window
          </label>
          <div className="flex flex-wrap gap-1.5">
            {WINDOWS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setWindowSeconds(option.value)}
                className={
                  windowSeconds === option.value
                    ? "rounded-lg bg-tg-primary/20 px-3 py-1.5 text-xs font-medium text-tg-accent"
                    : "rounded-lg px-3 py-1.5 text-xs font-medium text-tg-text-secondary hover:bg-tg-overlay/5"
                }
              >
                {option.label}
              </button>
            ))}
          </div>
          <p className="text-xs text-tg-text-muted">
            Measured from the first step, so it bounds the whole journey rather
            than each hop.
          </p>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={pending}
          >
            Cancel
          </Button>
          <Button type="submit" loading={pending} disabled={!valid}>
            {editing ? "Save" : "Create funnel"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
