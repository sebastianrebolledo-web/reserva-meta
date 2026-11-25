import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Genera un bundle standalone para Docker/Cloud Run
  output: "standalone",

  // Redirecciona todas las llamadas /api/v1/:path* al Backend Python (FastAPI con Google Workspace)
  async rewrites() {
    const backendUrl =
      process.env.BACKEND_INTERNAL_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://127.0.0.1:8000";

    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
