import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Configure Vite for the React development environment.
export default defineConfig({
  // Enable React JSX transformation and Fast Refresh.
  plugins: [react()],

  // Load shared environment variables from the project root.
  envDir: "..",

  server: {
    // Use a predictable local address for frontend-backend communication.
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
  },
});