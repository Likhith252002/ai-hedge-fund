import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Production env vars (set before running `npm run build`):
//   VITE_API_URL  — backend base URL, e.g. https://your-ec2-ip
//   VITE_WS_URL   — WebSocket base URL, e.g. wss://your-ec2-ip
//                   (omit both when deploying behind nginx on the same host —
//                    useWebSocket.js will derive the correct wss:// URL automatically)

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    port: 5173,
    // Dev proxy — production traffic goes through nginx on the same host
    proxy: mode === "development" ? {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/ws":  { target: "ws://localhost:8000",   changeOrigin: true, ws: true },
    } : undefined,
  },
}));
