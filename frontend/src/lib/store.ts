import { create } from "zustand";

interface AuthState {
  token: string | null;
  hydrated: boolean;
  setToken: (token: string) => void;
  logout: () => void;
  hydrate: () => void;
}

const STORAGE_KEY = "ava_token";

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  hydrated: false,
  setToken: (token: string) => {
    if (typeof window !== "undefined") localStorage.setItem(STORAGE_KEY, token);
    set({ token });
  },
  logout: () => {
    if (typeof window !== "undefined") localStorage.removeItem(STORAGE_KEY);
    set({ token: null });
  },
  hydrate: () => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem(STORAGE_KEY);
      set({ token, hydrated: true });
    }
  },
}));
