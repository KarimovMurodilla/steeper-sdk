import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";
import { ChatList } from "@/components/Chat/ChatList";
import { ChatWindow } from "@/components/Chat/ChatWindow";

export function ChatPage() {
  const { mobileChatOpen } = useUIStore();

  return (
    <div className="flex h-full">
      <div
        className={cn(
          "w-full border-r border-white/5 lg:w-80 xl:w-96",
          mobileChatOpen ? "hidden lg:block" : "block",
        )}
      >
        <div className="border-b border-white/5 bg-tg-bg-secondary/80 backdrop-blur-[20px] px-4 py-3">
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
