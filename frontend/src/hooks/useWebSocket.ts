import { useEffect, useRef, useCallback } from "react";
import { useAuthStore } from "@/store/authStore";
import { refreshAccessToken } from "@/api/client";
import type { WSDownlinkEnvelope, WSTopic, WSUplinkMessage } from "@/types/ws";

type MessageHandler = (envelope: WSDownlinkEnvelope) => void;

const PING_INTERVAL_MS = 25_000;
const RECONNECT_BASE_MS = 1_000;
const RECONNECT_MAX_MS = 30_000;

export function useWebSocket(onMessage: MessageHandler) {
  const wsRef = useRef<WebSocket | null>(null);
  const pingRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const reconnectDelay = useRef(RECONNECT_BASE_MS);
  // Keyed by target so a re-subscribe after a reconnect can be replayed
  // verbatim, topic included.
  const subscriptionsRef = useRef<Map<string, WSUplinkMessage>>(new Map());
  const mountedRef = useRef(true);

  // Keep the latest handler in a ref so the socket lifecycle does not depend on
  // its identity. Without this, the handler is recreated whenever the active
  // chat/bot changes, which would tear down and reconnect the socket on every
  // chat switch (dropping events and re-authenticating each time).
  const onMessageRef = useRef(onMessage);
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const getWsUrl = useCallback(() => {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = import.meta.env.VITE_WS_HOST || window.location.host;
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
      ws.send(JSON.stringify({ action: "authenticate", token: useAuthStore.getState().accessToken }));

      pingRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: "ping" }));
        }
      }, PING_INTERVAL_MS);

      subscriptionsRef.current.forEach((msg) => {
        ws.send(JSON.stringify(msg));
      });
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string);
        if (data.action === "pong") return;
        onMessageRef.current(data as WSDownlinkEnvelope);
      } catch {
        // ignore malformed JSON
      }
    };

    ws.onclose = (event) => {
      clearInterval(pingRef.current);
      if (!mountedRef.current) return;

      if (event.code === 1008) {
        // Auth was rejected (e.g. expired access token). Try a token refresh
        // before giving up; only log out if that fails. This avoids kicking the
        // operator out whenever the short-lived access token expires.
        refreshAccessToken()
          .then(() => {
            if (mountedRef.current) connect();
          })
          .catch(() => {
            useAuthStore.getState().logout();
          });
        return;
      }

      reconnectRef.current = setTimeout(() => {
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, RECONNECT_MAX_MS);
        connect();
      }, reconnectDelay.current);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [getWsUrl]);

  const subscribe = useCallback(
    (type: "chat_id" | "bot_id", id: string, topic?: WSTopic) => {
      const key = `${type}:${topic ?? ""}:${id}`;
      const msg = {
        action: "subscribe",
        [type]: id,
        ...(topic ? { topic } : {}),
      } as WSUplinkMessage;
      subscriptionsRef.current.set(key, msg);
      send(msg);
    },
    [send],
  );

  const unsubscribe = useCallback(
    (type: "chat_id" | "bot_id", id: string, topic?: WSTopic) => {
      const key = `${type}:${topic ?? ""}:${id}`;
      subscriptionsRef.current.delete(key);
      send({
        action: "unsubscribe",
        [type]: id,
        ...(topic ? { topic } : {}),
      } as WSUplinkMessage);
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
