import { NavLink } from "react-router-dom";
import {
  MessageSquare,
  Megaphone,
  BarChart3,
  Filter,
  ScrollText,
  LogOut,
  Command,
} from "lucide-react";
import { cn, displayName } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import { useUIStore } from "@/store/uiStore";
import { Avatar } from "@/components/ui/Avatar";
import { BotSwitcher } from "@/components/Bot/BotSwitcher";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

const navItems = [
  { to: "/chats", icon: MessageSquare, label: "Chats" },
  { to: "/broadcasts", icon: Megaphone, label: "Broadcasts" },
  { to: "/metrics", icon: BarChart3, label: "Analytics" },
  { to: "/funnels", icon: Filter, label: "Funnels" },
  { to: "/logs", icon: ScrollText, label: "Logs" },
];

export function Sidebar() {
  const { user, logout } = useAuthStore();
  const { sidebarOpen, setSidebarOpen, setCommandPaletteOpen } = useUIStore();

  return (
    <>
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-tg-overlay/5 bg-tg-bg-sidebar/80 backdrop-blur-[20px] transition-transform duration-300 lg:static lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center gap-3 border-b border-tg-overlay/5 px-5 py-4">
          <img
            src="/logo.png"
            alt="Steeper"
            className="h-9 w-9 rounded-xl object-cover shadow-lg shadow-tg-primary/20"
          />
          <span className="text-lg font-semibold tracking-tight">Steeper</span>
        </div>

        <nav aria-label="Main" className="flex-1 space-y-1 px-3 py-4">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                cn(
                  "relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tg-accent",
                  isActive
                    ? "bg-tg-primary/15 text-tg-accent before:absolute before:inset-y-1.5 before:-left-1 before:w-1 before:rounded-full before:bg-tg-accent"
                    : "text-tg-text-secondary hover:bg-tg-overlay/5 hover:text-tg-text",
                )
              }
            >
              <Icon size={20} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 pb-2">
          <ThemeToggle />
        </div>

        <div className="px-3 pb-2">
          <button
            onClick={() => setCommandPaletteOpen(true)}
            className="flex w-full items-center justify-between rounded-lg border border-tg-overlay/5 px-3 py-2 text-xs text-tg-text-muted transition-colors hover:bg-tg-overlay/5 hover:text-tg-text-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tg-accent"
          >
            <span className="flex items-center gap-2">
              <Command size={13} />
              Quick search
            </span>
            <kbd className="rounded border border-tg-overlay/10 px-1.5 py-0.5 font-mono text-[10px]">
              ⌘K
            </kbd>
          </button>
        </div>

        <div className="border-t border-tg-overlay/5 px-3 py-3">
          <BotSwitcher />
        </div>

        {user && (
          <div className="border-t border-tg-overlay/5 px-3 py-3">
            <div className="flex items-center gap-3 rounded-lg px-3 py-2">
              <Avatar
                name={displayName(user.first_name, user.last_name, user.username)}
                photoUrl={user.photo_url}
                size="sm"
              />
              <div className="flex-1 min-w-0">
                <p className="truncate text-sm font-medium">
                  {displayName(user.first_name, user.last_name)}
                </p>
                {user.username && (
                  <p className="truncate text-xs text-tg-text-muted">
                    @{user.username}
                  </p>
                )}
              </div>
              <button
                onClick={logout}
                className="rounded-lg p-1.5 text-tg-text-muted transition-colors hover:bg-tg-overlay/10 hover:text-tg-red focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tg-accent"
                title="Log out"
                aria-label="Log out"
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
