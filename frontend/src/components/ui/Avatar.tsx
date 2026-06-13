import { cn, getInitials } from "@/lib/utils";

interface Props {
  name: string;
  photoUrl?: string | null;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeMap = {
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-14 w-14 text-lg",
};

const colors = [
  "bg-blue-600",
  "bg-emerald-600",
  "bg-violet-600",
  "bg-rose-600",
  "bg-amber-600",
  "bg-cyan-600",
  "bg-pink-600",
  "bg-indigo-600",
];

function hashColor(name: string) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length]!;
}

export function Avatar({ name, photoUrl, size = "md", className }: Props) {
  if (photoUrl) {
    return (
      <img
        src={photoUrl}
        alt={name}
        className={cn(
          "rounded-full object-cover flex-shrink-0",
          sizeMap[size],
          className,
        )}
      />
    );
  }

  return (
    <div
      className={cn(
        "rounded-full flex-shrink-0 flex items-center justify-center font-semibold text-white",
        sizeMap[size],
        hashColor(name),
        className,
      )}
    >
      {getInitials(name)}
    </div>
  );
}
