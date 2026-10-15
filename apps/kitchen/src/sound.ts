// The kitchen buzzer. Browsers keep audio muted until someone touches the page, so one shared
// AudioContext is created and unlocked on the first touch, and the board shows a "tap to turn
// on sound" bar until then. The pattern is loud and rough on purpose: a kitchen is noisy.

let ctx: AudioContext | null = null;

function context(): AudioContext | null {
  if (typeof window === "undefined") return null;
  if (!ctx) {
    const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctor) return null;
    ctx = new Ctor();
  }
  return ctx;
}

/** True once the browser lets the page play sound. */
export function audioReady(): boolean {
  return context()?.state === "running";
}

/** Call from a touch or click: unlocks audio for the rest of the session. */
export async function unlockAudio(): Promise<boolean> {
  const c = context();
  if (!c) return false;
  if (c.state !== "running") await c.resume().catch(() => undefined);
  return c.state === "running";
}

function pulse(c: AudioContext, at: number, freq: number, length: number, volume: number): void {
  const osc = c.createOscillator();
  const gain = c.createGain();
  osc.type = "square";
  osc.frequency.setValueAtTime(freq, at);
  gain.gain.setValueAtTime(0.0001, at);
  gain.gain.exponentialRampToValueAtTime(volume, at + 0.015);
  gain.gain.setValueAtTime(volume, at + length - 0.03);
  gain.gain.exponentialRampToValueAtTime(0.0001, at + length);
  osc.connect(gain).connect(c.destination);
  osc.start(at);
  osc.stop(at + length + 0.02);
}

/** A new order: three rising double-buzzes, about 1.5 seconds. */
export function buzzNewOrder(): void {
  const c = context();
  if (!c || c.state !== "running") return;
  const t = c.currentTime + 0.02;
  for (let i = 0; i < 3; i++) {
    pulse(c, t + i * 0.5, 660 + i * 110, 0.16, 0.35);
    pulse(c, t + i * 0.5 + 0.2, 880 + i * 110, 0.16, 0.35);
  }
}

/** A reminder that an order is still waiting to be accepted: one short double-buzz. */
export function buzzReminder(): void {
  const c = context();
  if (!c || c.state !== "running") return;
  const t = c.currentTime + 0.02;
  pulse(c, t, 740, 0.14, 0.25);
  pulse(c, t + 0.2, 740, 0.14, 0.25);
}

const KEY = "diyneco.kitchen.sound";

export function soundPreference(): boolean {
  try {
    return localStorage.getItem(KEY) !== "off";
  } catch {
    return true;
  }
}

export function saveSoundPreference(on: boolean): void {
  try {
    localStorage.setItem(KEY, on ? "on" : "off");
  } catch {
    /* private mode: the choice lasts for this session only */
  }
}
