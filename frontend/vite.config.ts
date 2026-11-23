import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    // Served behind nginx on APP_PORT; HMR websocket goes through the same port.
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    hmr: { clientPort: Number(process.env.APP_PORT ?? 8000) },
    watch: { usePolling: true },
  },
});
