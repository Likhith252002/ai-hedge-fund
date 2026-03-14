import { useRef } from "react";

const wsUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
const url = `${wsUrl}/ws/analyse`;

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

    const ws = new WebSocket(url);
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
