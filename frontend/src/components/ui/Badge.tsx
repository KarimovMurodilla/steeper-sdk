import { cn } from "@/lib/utils";

interface Props {
  variant?: "success" | "warning" | "danger" | "info" | "neutral";
  children: React.ReactNode;
  className?: string;
}

const variants = {
  success: "bg-tg-green/20 text-tg-green",
  warning: "bg-tg-orange/20 text-tg-orange",
  danger: "bg-tg-red/20 text-tg-red",
  info: "bg-tg-primary/20 text-tg-accent",
  neutral: "bg-white/10 text-tg-text-secondary",
};

export function Badge({ variant = "neutral", children, className }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
