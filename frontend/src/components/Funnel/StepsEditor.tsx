import { useId } from "react";
import { ArrowDown, ArrowUp, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { MAX_FUNNEL_STEPS, MIN_FUNNEL_STEPS } from "@/hooks/useFunnels";
import { cn } from "@/lib/utils";
import type { EventName } from "@/types/api";

interface Props {
  steps: string[];
  onChange: (steps: string[]) => void;
  eventNames: EventName[];
  namesLoading?: boolean;
}

/**
 * The ordered step list.
 *
 * Each field is backed by a `datalist` of the event names this bot has actually
 * sent. That is the whole point of the suggestion endpoint: a step naming an
 * event that never existed produces a funnel of flat zeroes, which looks
 * exactly like real non-conversion and is close to undebuggable by eye.
 */
export function StepsEditor({
  steps,
  onChange,
  eventNames,
  namesLoading,
}: Props) {
  const listId = useId();

  const setStep = (index: number, value: string) =>
    onChange(steps.map((step, i) => (i === index ? value : step)));

  const addStep = () => onChange([...steps, ""]);

  const removeStep = (index: number) =>
    onChange(steps.filter((_, i) => i !== index));

  const moveStep = (index: number, delta: number) => {
    const target = index + delta;
    if (target < 0 || target >= steps.length) return;
    const next = [...steps];
    [next[index], next[target]] = [next[target]!, next[index]!];
    onChange(next);
  };

  const unknown = (step: string) =>
    step.trim().length > 0 &&
    eventNames.length > 0 &&
    !eventNames.some((event) => event.name === step);

  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between">
        <label className="block text-sm text-tg-text-secondary">Steps</label>
        <span className="text-xs text-tg-text-muted">
          {steps.length} of {MAX_FUNNEL_STEPS}
        </span>
      </div>

      <datalist id={listId}>
        {eventNames.map((event) => (
          <option key={event.name} value={event.name}>
            {event.count.toLocaleString()} events
          </option>
        ))}
      </datalist>

      {steps.map((step, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="w-5 shrink-0 text-center text-xs text-tg-text-muted">
            {i + 1}
          </span>

          <div className="flex-1">
            <input
              value={step}
              list={listId}
              onChange={(e) => setStep(i, e.target.value)}
              placeholder={i === 0 ? "e.g. signup" : "event name"}
              className={cn(
                "w-full rounded-lg border border-tg-overlay/10 bg-tg-overlay/5 px-3 py-2 text-sm text-tg-text placeholder:text-tg-text-muted outline-none transition-colors focus:border-tg-primary focus:ring-1 focus:ring-tg-primary/30",
                unknown(step) && "border-tg-orange/60",
              )}
            />
          </div>

          <div className="flex shrink-0 items-center gap-0.5">
            <IconButton
              label="Move up"
              disabled={i === 0}
              onClick={() => moveStep(i, -1)}
            >
              <ArrowUp size={14} />
            </IconButton>
            <IconButton
              label="Move down"
              disabled={i === steps.length - 1}
              onClick={() => moveStep(i, 1)}
            >
              <ArrowDown size={14} />
            </IconButton>
            <IconButton
              label="Remove step"
              disabled={steps.length <= MIN_FUNNEL_STEPS}
              onClick={() => removeStep(i)}
            >
              <X size={14} />
            </IconButton>
          </div>
        </div>
      ))}

      {steps.some(unknown) && (
        <p className="text-xs text-tg-orange">
          Highlighted steps name an event this bot has not sent in the last 90
          days. That is fine for an event you are about to ship, but a typo here
          reports as zero conversion.
        </p>
      )}

      {!namesLoading && eventNames.length === 0 && (
        <p className="text-xs text-tg-text-muted">
          This bot has not reported any events yet, so there is nothing to
          suggest. Steps you enter now will start matching once it does.
        </p>
      )}

      <Button
        type="button"
        variant="secondary"
        size="sm"
        onClick={addStep}
        disabled={steps.length >= MAX_FUNNEL_STEPS}
      >
        <Plus size={14} />
        Add step
      </Button>
    </div>
  );
}

function IconButton({
  label,
  disabled,
  onClick,
  children,
}: {
  label: string;
  disabled?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className="rounded-lg p-1.5 text-tg-text-muted transition-colors hover:bg-tg-overlay/10 hover:text-tg-text disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:bg-transparent"
    >
      {children}
    </button>
  );
}
