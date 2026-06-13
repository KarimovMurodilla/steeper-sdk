import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { Spinner } from "./Spinner";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, Props>(
  (
    {
      variant = "primary",
      size = "md",
      loading,
      disabled,
      className,
      children,
      ...props
    },
    ref,
  ) => {
    const variants = {
      primary:
        "bg-tg-primary text-white hover:bg-tg-primary-hover active:scale-[0.98]",
      secondary:
        "bg-white/5 text-tg-text hover:bg-white/10 border border-white/10",
      danger: "bg-tg-red/90 text-white hover:bg-tg-red active:scale-[0.98]",
      ghost: "text-tg-text-secondary hover:bg-white/5 hover:text-tg-text",
    };

    const sizes = {
      sm: "px-3 py-1.5 text-xs rounded-lg",
      md: "px-4 py-2.5 text-sm rounded-lg",
      lg: "px-6 py-3 text-base rounded-xl",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          "inline-flex items-center justify-center gap-2 font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed",
          variants[variant],
          sizes[size],
          className,
        )}
        {...props}
      >
        {loading && <Spinner size="sm" />}
        {children}
      </button>
    );
  },
);

Button.displayName = "Button";
