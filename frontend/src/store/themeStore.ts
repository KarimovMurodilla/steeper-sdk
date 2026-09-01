import { create } from "zustand";

export type ThemePreference = "system" | "light" | "dark";

const STORAGE_KEY = "steeper:theme";

function readStored(): ThemePreference {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (value === "light" || value === "dark" || value === "system") {
      return value;
    }
  } catch {
    // Private mode or blocked storage: fall back to following the OS.
  }
  return "system";
}

function systemTheme(): "light" | "dark" {
  return window.matchMedia("(prefers-color-scheme: light)").matches
    ? "light"
    : "dark";
}

/** Writes the resolved theme onto <html data-theme>, which drives the CSS vars. */
function apply(preference: ThemePreference): "light" | "dark" {
  const resolved = preference === "system" ? systemTheme() : preference;
  document.documentElement.dataset.theme = resolved;
  return resolved;
}

interface ThemeState {
  preference: ThemePreference;
  resolved: "light" | "dark";
  setPreference: (preference: ThemePreference) => void;
}

const initialPreference = readStored();

export const useThemeStore = create<ThemeState>((set) => ({
  preference: initialPreference,
  resolved: apply(initialPreference),

  setPreference: (preference) => {
    try {
      localStorage.setItem(STORAGE_KEY, preference);
    } catch {
      // Not being able to persist the choice must not break switching it.
    }
    set({ preference, resolved: apply(preference) });
  },
}));

// Follow the OS while the preference is "system".
window
  .matchMedia("(prefers-color-scheme: light)")
  .addEventListener("change", () => {
    const { preference } = useThemeStore.getState();
    if (preference === "system") {
      useThemeStore.setState({ resolved: apply("system") });
    }
  });
