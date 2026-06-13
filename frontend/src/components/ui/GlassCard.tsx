import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface Props {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

export function GlassCard({ children, className, onClick }: Props) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "rounded-xl border border-white/5 bg-white/5 backdrop-blur-[20px] shadow-lg",
        onClick && "cursor-pointer hover:bg-white/10 transition-colors",
        className,
      )}
    >
      {children}
    </div>
  );
}
