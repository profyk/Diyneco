"use client";

import { useCallback, useEffect, useState } from "react";

import { Icon } from "./icons";
import { cn } from "./primitives";
import { THEME_KEY } from "./theme-script";

// Light, dark or follow the device. The choice is remembered per device and applied before the
// first paint by THEME_SCRIPT (put it in the root layout's <head>), so pages never flash.

export type ThemeChoice = "light" | "dark" | "system";

const KEY = THEME_KEY;

function read(): ThemeChoice {
  try {
    const t = localStorage.getItem(KEY);
    return t === "light" || t === "dark" ? t : "system";
  } catch {
    return "system";
  }
}

function apply(choice: ThemeChoice): void {
  const root = document.documentElement;
  if (choice === "system") delete root.dataset.theme;
  else root.dataset.theme = choice;
  try {
    if (choice === "system") localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, choice);
  } catch {
    /* private mode: the choice lasts until the page closes */
  }
}

export function useTheme(): [ThemeChoice, (choice: ThemeChoice) => void] {
  const [choice, setChoice] = useState<ThemeChoice>("system");
  useEffect(() => setChoice(read()), []);
  const set = useCallback((next: ThemeChoice) => {
    apply(next);
    setChoice(next);
  }, []);
  return [choice, set];
}

const OPTIONS: { value: ThemeChoice; label: string; icon: "sun" | "moon" | "monitor" }[] = [
  { value: "light", label: "Light", icon: "sun" },
  { value: "dark", label: "Dark", icon: "moon" },
  { value: "system", label: "Same as device", icon: "monitor" },
];

/** Three-way switch: light, dark, same as the device. */
export function ThemeSwitch({ className }: { className?: string }) {
  const [choice, setChoice] = useTheme();
  return (
    <div role="radiogroup" aria-label="Colour theme" className={cn("inline-flex rounded-full border border-line bg-surface-2 p-0.5", className)}>
      {OPTIONS.map((o) => (
        <button
          key={o.value}
          type="button"
          role="radio"
          aria-checked={choice === o.value}
          aria-label={o.label}
          title={o.label}
          onClick={() => setChoice(o.value)}
          className={cn(
            "flex size-8 items-center justify-center rounded-full transition",
            choice === o.value ? "bg-surface text-ink shadow-sm" : "text-muted hover:text-ink",
          )}
        >
          <Icon name={o.icon} className="size-4" />
        </button>
      ))}
    </div>
  );
}
