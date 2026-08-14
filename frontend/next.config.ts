import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.ticketm.net",
        pathname: "/dam/**",
      },
    ],
  },
};

export default nextConfig;
