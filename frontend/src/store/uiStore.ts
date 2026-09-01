import { create } from "zustand";

interface UIState {
  sidebarOpen: boolean;
  activeBotId: string | null;
  activeChatId: string | null;
  mobileChatOpen: boolean;
  commandPaletteOpen: boolean;
  /**
   * Client-side unread counters, keyed by chat id. The API does not track read
   * state, so these only count live messages that arrived while the chat was
   * closed, and they reset on reload.
   */
  unread: Record<string, number>;
  setSidebarOpen: (open: boolean) => void;
  setActiveBotId: (id: string | null) => void;
  setActiveChatId: (id: string | null) => void;
  setMobileChatOpen: (open: boolean) => void;
  setCommandPaletteOpen: (open: boolean) => void;
  bumpUnread: (chatId: string) => void;
  clearUnread: (chatId: string) => void;
}

function withoutChat(unread: Record<string, number>, chatId: string) {
  if (!(chatId in unread)) return unread;
  const next = { ...unread };
  delete next[chatId];
  return next;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  activeBotId: null,
  activeChatId: null,
  mobileChatOpen: false,
  commandPaletteOpen: false,
  unread: {},

  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  // Unread counters belong to one bot's chats, so a bot switch clears them.
  setActiveBotId: (id) =>
    set({ activeBotId: id, activeChatId: null, unread: {} }),
  setActiveChatId: (id) =>
    set((state) => ({
      activeChatId: id,
      unread: id ? withoutChat(state.unread, id) : state.unread,
    })),
  setMobileChatOpen: (open) => set({ mobileChatOpen: open }),
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),

  bumpUnread: (chatId) =>
    set((state) => ({
      unread: { ...state.unread, [chatId]: (state.unread[chatId] ?? 0) + 1 },
    })),
  clearUnread: (chatId) =>
    set((state) => ({ unread: withoutChat(state.unread, chatId) })),
}));
