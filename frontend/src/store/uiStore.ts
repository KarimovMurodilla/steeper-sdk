import { create } from "zustand";

interface UIState {
  sidebarOpen: boolean;
  activeBotId: string | null;
  activeChatId: string | null;
  mobileChatOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  setActiveBotId: (id: string | null) => void;
  setActiveChatId: (id: string | null) => void;
  setMobileChatOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  activeBotId: null,
  activeChatId: null,
  mobileChatOpen: false,

  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setActiveBotId: (id) => set({ activeBotId: id, activeChatId: null }),
  setActiveChatId: (id) => set({ activeChatId: id }),
  setMobileChatOpen: (open) => set({ mobileChatOpen: open }),
}));
