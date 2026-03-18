import { useRef } from "react";

function resolveWsUrl() {
  // Explicit override wins (set at build time via VITE_WS_URL env var).
  if (import.meta.env.VITE_WS_URL) {
    return `${import.meta.env.VITE_WS_URL}/ws/analyse`;
  }
  // In production (non-localhost), derive wss:// from the page origin so
  // nginx can proxy /ws/* without needing a separate port in the URL.
  if (window.location.hostname !== "localhost") {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://${window.location.host}/ws/analyse`;
  }
  return "ws://localhost:8000/ws/analyse";
}

/**
 * useWebSocket
 * Manages a single WebSocket connection to /ws/analyse.
 * Returns { connect, disconnect, wsRef }.
 */
export function useWebSocket() {
  const wsRef = useRef(null);

  function connect({ onOpen, onMessage, onError, onClose } = {}) {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const ws = new WebSocket(resolveWsUrl());
    wsRef.current = ws;

    if (onOpen)    ws.onopen    = onOpen;
    if (onMessage) ws.onmessage = onMessage;
    if (onError)   ws.onerror   = onError;
    if (onClose)   ws.onclose   = onClose;

    return ws;
  }

  function disconnect() {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }

  return { connect, disconnect, wsRef };
}
