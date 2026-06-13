import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, Props>(
  ({ label, error, className, ...props }, ref) => {
    return (
      <div className="space-y-1.5">
        {label && (
          <label className="block text-sm text-tg-text-secondary">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={cn(
            "w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-tg-text placeholder:text-tg-text-muted outline-none transition-colors focus:border-tg-primary focus:ring-1 focus:ring-tg-primary/30",
            error && "border-tg-red focus:border-tg-red",
            className,
          )}
          {...props}
        />
        {error && <p className="text-xs text-tg-red">{error}</p>}
      </div>
    );
  },
);

Input.displayName = "Input";
