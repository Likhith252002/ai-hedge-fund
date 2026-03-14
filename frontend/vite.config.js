import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    port: 5173,
    // Dev proxy only — production uses VITE_API_URL / VITE_WS_URL env vars
    proxy: mode === "development" ? {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/ws":  { target: "ws://localhost:8000",   changeOrigin: true, ws: true },
    } : undefined,
  },
}));
