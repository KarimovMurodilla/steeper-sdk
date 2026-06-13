import { useEffect, useRef, useCallback } from "react";
import { useAuthStore } from "@/store/authStore";
import type { WSDownlinkEnvelope, WSUplinkMessage } from "@/types/ws";

type MessageHandler = (envelope: WSDownlinkEnvelope) => void;

const PING_INTERVAL_MS = 25_000;
const RECONNECT_BASE_MS = 1_000;
const RECONNECT_MAX_MS = 30_000;

export function useWebSocket(onMessage: MessageHandler) {
  const wsRef = useRef<WebSocket | null>(null);
  const pingRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const reconnectDelay = useRef(RECONNECT_BASE_MS);
  const subscriptionsRef = useRef<Set<string>>(new Set());
  const mountedRef = useRef(true);

  const getWsUrl = useCallback(() => {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = import.meta.env.VITE_WS_HOST ?? window.location.host;
    return `${proto}//${host}/v1/ws`;
  }, []);

  const send = useCallback((msg: WSUplinkMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const connect = useCallback(() => {
    const token = useAuthStore.getState().accessToken;
    if (!token || !mountedRef.current) return;

    const ws = new WebSocket(getWsUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectDelay.current = RECONNECT_BASE_MS;
      ws.send(JSON.stringify({ action: "authenticate", token }));

      pingRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: "ping" }));
        }
      }, PING_INTERVAL_MS);

      subscriptionsRef.current.forEach((key) => {
        const [type, id] = key.split(":");
        if (type && id) {
          send({ action: "subscribe", [type]: id } as WSUplinkMessage);
        }
      });
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string);
        if (data.action === "pong") return;
        onMessage(data as WSDownlinkEnvelope);
      } catch {
        // ignore malformed JSON
      }
    };

    ws.onclose = (event) => {
      clearInterval(pingRef.current);

      if (event.code === 1008) {
        useAuthStore.getState().logout();
        return;
      }

      if (mountedRef.current) {
        reconnectRef.current = setTimeout(() => {
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, RECONNECT_MAX_MS);
          connect();
        }, reconnectDelay.current);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [getWsUrl, onMessage, send]);

  const subscribe = useCallback(
    (type: "chat_id" | "bot_id", id: string) => {
      const key = `${type}:${id}`;
      subscriptionsRef.current.add(key);
      send({ action: "subscribe", [type]: id } as WSUplinkMessage);
    },
    [send],
  );

  const unsubscribe = useCallback(
    (type: "chat_id" | "bot_id", id: string) => {
      const key = `${type}:${id}`;
      subscriptionsRef.current.delete(key);
      send({ action: "unsubscribe", [type]: id } as WSUplinkMessage);
    },
    [send],
  );

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      clearInterval(pingRef.current);
      clearTimeout(reconnectRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { subscribe, unsubscribe, send };
}
