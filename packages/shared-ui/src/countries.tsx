"use client";

/**
 * Flags, a searchable country picker and an international phone field (D84).
 * Flags are SVGs from flag-icons (emoji flags show as letters on Windows).
 * Import from "@diyneco/shared-ui/countries" so only the apps that use them load the flag styles.
 */
import "flag-icons/css/flag-icons.min.css";

import { type KeyboardEvent, useEffect, useId, useMemo, useRef, useState } from "react";

import { cn } from "./primitives";

export interface CountryOption {
  code: string;
  name: string;
  dial?: string;
}

/** A country's flag; `code` is ISO 3166-1 alpha-2 ("ZA"). */
export function Flag({ code, title, className }: { code: string; title?: string; className?: string }) {
  return (
    <span
      role={title ? "img" : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
      className={cn(
        "fi inline-block shrink-0 rounded-[3px] bg-cover shadow-[0_0_0_1px_rgba(11,35,80,0.12)]",
        `fi-${code.toLowerCase()}`,
        className ?? "h-[0.9em] w-[1.2em]",
      )}
    />
  );
}

function fold(s: string): string {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function matches(c: CountryOption, q: string): boolean {
  if (!q) return true;
  const f = fold(q.trim());
  const digits = f.replace(/[^\d]/g, "");
  return (
    fold(c.name).includes(f) ||
    c.code.toLowerCase() === f ||
    (digits.length > 0 && (c.dial ?? "").replace("+", "").startsWith(digits))
  );
}

/**
 * Type-to-search country picker (combobox): arrow keys move, Enter picks, Escape closes.
 * `fieldProps` are the props Field hands to its control (id, aria-describedby, aria-invalid).
 */
export function CountryPicker({
  countries,
  value,
  onChange,
  placeholder = "Search for a country",
  showDial = false,
  fieldProps,
  className,
}: {
  countries: CountryOption[];
  value: string;
  onChange: (code: string) => void;
  placeholder?: string;
  showDial?: boolean;
  fieldProps?: { id: string; "aria-describedby"?: string; "aria-invalid"?: boolean };
  className?: string;
}) {
  const listId = useId();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const box = useRef<HTMLDivElement>(null);
  const list = useRef<HTMLUListElement>(null);
  const selected = countries.find((c) => c.code === value);
  const shown = useMemo(() => countries.filter((c) => matches(c, query)), [countries, query]);

  useEffect(() => {
    const close = (e: MouseEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);
  useEffect(() => setActive(0), [query]);
  useEffect(() => {
    list.current?.querySelector<HTMLElement>(`[data-index="${active}"]`)?.scrollIntoView({ block: "nearest" });
  }, [active, open]);

  const pick = (c: CountryOption) => {
    onChange(c.code);
    setQuery("");
    setOpen(false);
  };
  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setActive((i) => Math.min(i + 1, shown.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && open && shown[active]) {
      e.preventDefault();
      pick(shown[active]);
    } else if (e.key === "Escape") {
      setOpen(false);
      setQuery("");
    }
  };

  return (
    <div ref={box} className={cn("relative", className)}>
      <div
        className={cn(
          "flex h-10 w-full items-center gap-2 rounded-[10px] border border-line bg-surface px-3 text-sm",
          "focus-within:border-blue",
          fieldProps?.["aria-invalid"] && "border-crit",
        )}
      >
        {selected && !open ? <Flag code={selected.code} /> : <SearchIcon />}
        <input
          {...fieldProps}
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={open && shown[active] ? `${listId}-${shown[active].code}` : undefined}
          autoComplete="off"
          spellCheck={false}
          className="min-w-0 flex-1 bg-transparent text-ink placeholder:text-muted focus:outline-none"
          placeholder={selected ? selected.name : placeholder}
          value={open ? query : selected ? selected.name : ""}
          onFocus={() => setOpen(true)}
          onClick={() => setOpen(true)}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onKeyDown={onKey}
        />
        <svg viewBox="0 0 20 20" className="size-4 shrink-0 text-muted" aria-hidden>
          <path d="M5 8l5 5 5-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      </div>
      {open ? (
        <ul
          ref={list}
          id={listId}
          role="listbox"
          className="absolute z-30 mt-1 max-h-72 w-full overflow-auto rounded-[10px] border border-line bg-surface py-1 shadow-lg"
        >
          {shown.length === 0 ? (
            <li className="px-3 py-2 text-sm text-muted">No country matches “{query}”.</li>
          ) : (
            shown.map((c, i) => (
              <li
                key={c.code}
                id={`${listId}-${c.code}`}
                data-index={i}
                role="option"
                aria-selected={c.code === value}
                onMouseDown={(e) => e.preventDefault()}
                onMouseEnter={() => setActive(i)}
                onClick={() => pick(c)}
                className={cn(
                  "flex cursor-pointer items-center gap-2.5 px-3 py-2 text-sm text-ink",
                  i === active && "bg-surface-2",
                  c.code === value && "font-medium",
                )}
              >
                <Flag code={c.code} />
                <span className="flex-1 truncate">{c.name}</span>
                {showDial && c.dial ? <span className="text-xs tabular-nums text-muted">{c.dial}</span> : null}
              </li>
            ))
          )}
        </ul>
      ) : null}
    </div>
  );
}

function SearchIcon() {
  return (
    <svg viewBox="0 0 20 20" className="size-4 shrink-0 text-muted" aria-hidden>
      <circle cx="9" cy="9" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="M13.5 13.5L17 17" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

/** The E.164 form ("+27821234567") of a national number typed in any style, or "" if empty. */
export function toE164(dial: string, national: string): string {
  const digits = national.replace(/[^\d]/g, "").replace(/^0+/, "");
  return digits ? `${dial}${digits}` : "";
}

/**
 * International phone field: a country (flag and dialling code) plus the number as people
 * write it locally. Reports the E.164 form, which is what the API stores.
 */
export function PhoneInput({
  countries,
  country,
  onCountryChange,
  number,
  onNumberChange,
  fieldProps,
  placeholder = "Mobile number",
}: {
  countries: (CountryOption & { dial: string })[];
  country: string;
  onCountryChange: (code: string) => void;
  number: string;
  onNumberChange: (national: string) => void;
  fieldProps?: { id: string; "aria-describedby"?: string; "aria-invalid"?: boolean };
  placeholder?: string;
}) {
  const current = countries.find((c) => c.code === country);
  return (
    <div className="flex gap-2">
      <label className="relative flex h-10 shrink-0 items-center gap-1.5 rounded-[10px] border border-line bg-surface pl-3 pr-2 text-sm focus-within:border-blue">
        {current ? <Flag code={current.code} /> : null}
        <span className="tabular-nums text-ink">{current?.dial ?? "+"}</span>
        <svg viewBox="0 0 20 20" className="size-3.5 text-muted" aria-hidden>
          <path d="M5 8l5 5 5-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
        <select
          aria-label="Country dialling code"
          className="absolute inset-0 cursor-pointer opacity-0"
          value={country}
          onChange={(e) => onCountryChange(e.target.value)}
        >
          {countries.map((c) => (
            <option key={c.code} value={c.code}>
              {c.name} ({c.dial})
            </option>
          ))}
        </select>
      </label>
      <input
        {...fieldProps}
        type="tel"
        inputMode="tel"
        autoComplete="tel-national"
        placeholder={placeholder}
        className={cn(
          "h-10 w-full min-w-0 rounded-[10px] border border-line bg-surface px-3 text-sm text-ink placeholder:text-muted",
          "focus:border-blue focus:outline-none aria-[invalid=true]:border-crit",
        )}
        value={number}
        onChange={(e) => onNumberChange(e.target.value)}
      />
    </div>
  );
}
