import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Habilita o suporte do Vite aos componentes React escritos em JSX.
export default defineConfig({
  plugins: [react()],
});
