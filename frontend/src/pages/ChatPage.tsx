import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";
import { useActiveBot } from "@/hooks/useActiveBot";
import { ChatList } from "@/components/Chat/ChatList";
import { ChatWindow } from "@/components/Chat/ChatWindow";

export function ChatPage() {
  const { mobileChatOpen } = useUIStore();
  // Resolves / auto-selects the active bot used across the app.
  useActiveBot();

  return (
    <div className="flex h-full">
      <div
        className={cn(
          "flex w-full flex-col border-r border-white/5 lg:w-80 xl:w-96",
          mobileChatOpen ? "hidden lg:flex" : "flex",
        )}
      >
        <div className="flex items-center justify-between gap-2 border-b border-white/5 bg-tg-bg-secondary/80 px-4 py-3 backdrop-blur-[20px]">
          <h2 className="font-semibold">Chats</h2>
        </div>
        <ChatList />
      </div>
      <div
        className={cn(
          "flex-1",
          mobileChatOpen ? "block" : "hidden lg:block",
        )}
      >
        <ChatWindow />
      </div>
    </div>
  );
}
