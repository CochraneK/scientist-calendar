import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { copyFileSync, mkdirSync } from "node:fs";
import { fileURLToPath, URL } from "node:url";

// 静态站额外文件：构建后复制到输出目录（不会被 emptyOutDir 清掉）。
function copyExtras() {
  return {
    name: "copy-docs-extras",
    closeBundle() {
      const outDir = fileURLToPath(new URL("../../docs", import.meta.url));
      for (const name of ["backup-candidates.md"]) {
        mkdirSync(outDir, { recursive: true });
        copyFileSync(new URL(`./extras/${name}`, import.meta.url), `${outDir}/${name}`);
      }
    },
  };
}

export default defineConfig({
  root: fileURLToPath(new URL(".", import.meta.url)),
  base: "/scientist-calendar/",
  publicDir: "../../public",
  plugins: [react(), copyExtras()],
  build: {
    outDir: "../../docs",
    emptyOutDir: true,
  },
});
