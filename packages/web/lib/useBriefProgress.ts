import { useCallback, useEffect, useRef, useState } from "react";
import type { ProgressEvent } from "./types/progress";

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_API_WS_URL || "ws://localhost:8000";
const MAX_RETRIES = 3;
const BACKOFF_MS = [1000, 2000, 4000];

interface BriefProgressState {
  events: Map<string, ProgressEvent>;
  isConnected: boolean;
}

export function useBriefProgress(
  briefId: string | null,
): BriefProgressState {
  const [events, setEvents] = useState<Map<string, ProgressEvent>>(
    () => new Map(),
  );
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (!briefId) return;
    retryTimeoutRef.current = null;

    const url = `${WS_BASE_URL}/ws/briefs/${briefId}/progress`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      retriesRef.current = 0;
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data: ProgressEvent = JSON.parse(event.data);
        setEvents((prev) => {
          const next = new Map(prev);
          next.set(data.job_id, data);
          return next;
        });
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
      if (retriesRef.current < MAX_RETRIES) {
        const delay = BACKOFF_MS[retriesRef.current] ?? BACKOFF_MS[BACKOFF_MS.length - 1];
        retriesRef.current += 1;
        retryTimeoutRef.current = setTimeout(connect, delay);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [briefId]);

  useEffect(() => {
    if (!briefId) {
      setEvents(new Map());
      setIsConnected(false);
      return;
    }

    connect();

    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [briefId, connect]);

  return { events, isConnected };
}
