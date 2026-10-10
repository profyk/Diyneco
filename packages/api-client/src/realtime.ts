/**
 * Realtime client for the API's WebSocket gateway (API spec, Realtime WebSocket protocol).
 *
 * Events are notifications, not data: on an event the app refetches over REST, so a lost or
 * reordered event can never corrupt what is shown. The client authenticates, subscribes with
 * the last `seq` it processed (the server replays the last 24 hours), answers pings, ignores
 * events it has already seen, and reconnects with exponential back-off and jitter
 * (1 s, 2 s, 4 s … 30 s). While disconnected the app should poll; `onStatus` tells it when.
 */

export interface RealtimeEvent {
  op: "event";
  seq: number;
  event_id: string;
  type: string;
  channel: string;
  occurred_at: string;
  data: Record<string, unknown>;
  hotel_id?: string | null;
}

export type RealtimeStatus = "connecting" | "live" | "offline";

export interface RealtimeOptions {
  /** API origin, e.g. "https://api.diyneco.com". */
  baseUrl: string;
  getToken: () => string | null | Promise<string | null>;
  /** Which of the allowed channels to join; default all the server offers. */
  channels?: (allowed: string[]) => string[];
  onEvent: (event: RealtimeEvent) => void;
  onStatus?: (status: RealtimeStatus) => void;
  /** Close codes 4409 (device rebound) and 4410 (hotel suspended) end the session. */
  onFatal?: (code: number, reason: string) => void;
  WebSocketImpl?: typeof WebSocket;
}

const FATAL = new Set([4409, 4410]);

export function wsUrl(baseUrl: string): string {
  return `${baseUrl.replace(/^http/, "ws").replace(/\/$/, "")}/api/v1/ws`;
}

export function connectRealtime(options: RealtimeOptions): { close: () => void } {
  const WS = options.WebSocketImpl ?? WebSocket;
  let socket: WebSocket | null = null;
  let stopped = false;
  let attempt = 0;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let lastSeq = 0;
  const seen = new Set<string>();

  const status = (s: RealtimeStatus) => options.onStatus?.(s);

  function schedule() {
    if (stopped) return;
    status("offline");
    const delay = Math.min(30_000, 1000 * 2 ** attempt) * (0.75 + Math.random() * 0.5);
    attempt += 1;
    timer = setTimeout(open, delay);
  }

  async function open() {
    if (stopped) return;
    status("connecting");
    const token = await options.getToken();
    if (!token) {
      schedule();
      return;
    }
    const ws = new WS(wsUrl(options.baseUrl));
    socket = ws;
    ws.onopen = () => ws.send(JSON.stringify({ op: "auth", token }));
    ws.onmessage = (msg) => {
      let data: Record<string, unknown>;
      try {
        data = JSON.parse(String(msg.data));
      } catch {
        return;
      }
      switch (data.op) {
        case "ready": {
          const allowed = (data.channels as string[]) ?? [];
          const channels = options.channels ? options.channels(allowed) : allowed;
          if (channels.length === 0) return;
          ws.send(JSON.stringify({ op: "subscribe", channels, since_seq: lastSeq }));
          break;
        }
        case "subscribed":
          attempt = 0;
          status("live");
          if (typeof data.seq === "number" && data.seq > lastSeq && lastSeq === 0) lastSeq = data.seq;
          break;
        case "ping":
          ws.send(JSON.stringify({ op: "pong" }));
          break;
        case "event": {
          const event = data as unknown as RealtimeEvent;
          if (seen.has(event.event_id)) return;
          seen.add(event.event_id);
          if (seen.size > 2000) seen.clear();
          if (event.channel !== "platform" && event.seq > lastSeq) lastSeq = event.seq;
          options.onEvent(event);
          break;
        }
      }
    };
    ws.onclose = (ev) => {
      socket = null;
      if (FATAL.has(ev.code)) {
        stopped = true;
        status("offline");
        options.onFatal?.(ev.code, ev.reason);
        return;
      }
      schedule();
    };
    ws.onerror = () => ws.close();
  }

  void open();
  return {
    close() {
      stopped = true;
      if (timer) clearTimeout(timer);
      socket?.close(1000, "bye");
    },
  };
}
