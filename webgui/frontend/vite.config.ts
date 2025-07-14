import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [tailwindcss(), sveltekit()],
  build: {
    outDir: path.resolve(__dirname, "../frontend/public"), // adjust to match Flask's static folder
    emptyOutDir: true,
  },
});
