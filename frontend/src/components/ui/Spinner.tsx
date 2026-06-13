import { cn } from "@/lib/utils";

interface Props {
  className?: string;
  size?: "sm" | "md" | "lg";
}

const sizeMap = { sm: "h-4 w-4", md: "h-6 w-6", lg: "h-10 w-10" };

export function Spinner({ className, size = "md" }: Props) {
  return (
    <div
      className={cn(
        "animate-spin rounded-full border-2 border-tg-text-muted border-t-tg-primary",
        sizeMap[size],
        className,
      )}
    />
  );
}
