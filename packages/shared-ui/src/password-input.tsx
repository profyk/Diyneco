"use client";

import { forwardRef, type InputHTMLAttributes, useEffect, useState } from "react";

import { cn, controlClass } from "./primitives";

/**
 * A password or PIN field with an eye button that shows what was typed. It always starts
 * hidden, and goes back to hidden when the form is submitted (the value is not kept visible
 * on a shared screen).
 */
export const PasswordInput = forwardRef<HTMLInputElement, Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & { revealLabel?: string }>(
  function PasswordInput({ className, revealLabel = "password", ...rest }, ref) {
    const [shown, setShown] = useState(false);
    useEffect(() => {
      const form = (rest.id ? document.getElementById(rest.id) : null)?.closest("form");
      if (!form) return;
      const hide = () => setShown(false);
      form.addEventListener("submit", hide);
      return () => form.removeEventListener("submit", hide);
    }, [rest.id]);
    return (
      <div className="relative">
        <input ref={ref} type={shown ? "text" : "password"} className={cn(controlClass, "h-10 pr-11", className)} {...rest} />
        <button
          type="button"
          onClick={() => setShown((v) => !v)}
          aria-label={shown ? `Hide ${revealLabel}` : `Show ${revealLabel}`}
          aria-pressed={shown}
          title={shown ? `Hide ${revealLabel}` : `Show ${revealLabel}`}
          className="absolute inset-y-0 right-1 my-auto flex size-9 items-center justify-center rounded-md text-muted hover:bg-surface-2 hover:text-ink focus-visible:outline-2 focus-visible:outline-blue"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            {shown ? (
              <>
                <path d="M3 3l18 18" />
                <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
                <path d="M9.9 5.1A9.8 9.8 0 0 1 12 5c5 0 9 4.5 10 7a12.6 12.6 0 0 1-3.2 4.3M6.6 6.6C4.3 8 2.7 10.1 2 12c1 2.5 5 7 10 7 1.6 0 3-.4 4.3-1" />
              </>
            ) : (
              <>
                <path d="M2 12c1-2.5 5-7 10-7s9 4.5 10 7c-1 2.5-5 7-10 7S3 14.5 2 12z" />
                <circle cx="12" cy="12" r="3" />
              </>
            )}
          </svg>
        </button>
      </div>
    );
  },
);
