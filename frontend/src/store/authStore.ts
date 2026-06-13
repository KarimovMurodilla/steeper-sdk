import { create } from "zustand";
import type { UserProfileViewModel } from "@/types/api";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserProfileViewModel | null;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: UserProfileViewModel) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

const TOKEN_KEY = "steeper_access_token";
const REFRESH_KEY = "steeper_refresh_token";

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: localStorage.getItem(TOKEN_KEY),
  refreshToken: localStorage.getItem(REFRESH_KEY),
  user: null,

  setTokens: (access, refresh) => {
    localStorage.setItem(TOKEN_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
    set({ accessToken: access, refreshToken: refresh });
  },

  setUser: (user) => set({ user }),

  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    set({ accessToken: null, refreshToken: null, user: null });
  },

  isAuthenticated: () => !!get().accessToken,
}));
