import { Menu } from "lucide-react";
import { useUIStore } from "@/store/uiStore";

/**
 * Mobile-only header. The sidebar toggle lives here rather than floating over
 * the page, where it used to sit on top of the chat composer.
 */
export function MobileTopBar() {
  const { setSidebarOpen } = useUIStore();

  return (
    <header className="flex flex-shrink-0 items-center gap-3 border-b border-tg-overlay/5 bg-tg-bg-secondary/80 px-3 py-2.5 backdrop-blur-[20px] lg:hidden">
      <button
        onClick={() => setSidebarOpen(true)}
        aria-label="Open navigation"
        className="rounded-lg p-2 text-tg-text-secondary transition-colors hover:bg-tg-overlay/10 hover:text-tg-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tg-accent"
      >
        <Menu size={20} />
      </button>
      <img src="/logo.png" alt="" className="h-7 w-7 rounded-lg" />
      <span className="font-semibold tracking-tight">Steeper</span>
    </header>
  );
}
