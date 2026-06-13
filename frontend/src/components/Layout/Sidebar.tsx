import { NavLink } from "react-router-dom";
import {
  Bot,
  MessageSquare,
  Megaphone,
  BarChart3,
  LogOut,
  Menu,
} from "lucide-react";
import { cn, displayName } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import { useUIStore } from "@/store/uiStore";
import { Avatar } from "@/components/ui/Avatar";

const navItems = [
  { to: "/", icon: Bot, label: "Bots" },
  { to: "/chats", icon: MessageSquare, label: "Chats" },
  { to: "/broadcasts", icon: Megaphone, label: "Broadcasts" },
  { to: "/analytics", icon: BarChart3, label: "Analytics" },
];

export function Sidebar() {
  const { user, logout } = useAuthStore();
  const { sidebarOpen, setSidebarOpen } = useUIStore();

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
          "fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-white/5 bg-tg-bg-sidebar/80 backdrop-blur-[20px] transition-transform duration-300 lg:static lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center gap-3 border-b border-white/5 px-5 py-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-tg-primary font-bold text-white">
            S
          </div>
          <span className="text-lg font-semibold tracking-tight">Steeper</span>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-tg-primary/15 text-tg-accent"
                    : "text-tg-text-secondary hover:bg-white/5 hover:text-tg-text",
                )
              }
            >
              <Icon size={20} />
              {label}
            </NavLink>
          ))}
        </nav>

        {user && (
          <div className="border-t border-white/5 px-3 py-3">
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
                className="rounded-lg p-1.5 text-tg-text-muted hover:bg-white/10 hover:text-tg-red transition-colors"
                title="Log out"
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        )}
      </aside>

      <button
        onClick={() => setSidebarOpen(true)}
        className="fixed bottom-4 left-4 z-10 rounded-full bg-tg-primary p-3 shadow-lg lg:hidden"
      >
        <Menu size={20} />
      </button>
    </>
  );
}
