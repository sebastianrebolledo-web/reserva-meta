import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Genera un bundle standalone para Docker/Cloud Run
  // Incluye solo los archivos necesarios para producción
  output: "standalone",
};

export default nextConfig;
