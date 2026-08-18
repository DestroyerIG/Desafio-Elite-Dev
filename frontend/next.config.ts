import type { NextConfig } from "next";

const publicApiUrl = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");
const internalApiUrl = (process.env.INTERNAL_API_URL ?? publicApiUrl).replace(
  /\/$/,
  "",
);

const nextConfig: NextConfig = {
  // O modo standalone existe para a imagem Docker, que copia `.next/standalone`
  // e executa `server.js`. Na Vercel ele quebra o build: o rastreamento de
  // arquivos vai para dentro de `standalone/` em vez de emitir os `.nft.json` na
  // raiz de `.next`, que é onde a plataforma os procura ao montar as funções.
  output: process.env.VERCEL ? undefined : "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.ticketm.net",
        pathname: "/dam/**",
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/uploads/:path*",
        destination: `${internalApiUrl}/uploads/:path*`,
      },
    ];
  },
};

export default nextConfig;
