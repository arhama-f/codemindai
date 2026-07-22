import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Only affects `next build`'s output shape (used by apps/web/Dockerfile);
  // has no effect on `next dev`.
  output: "standalone",
};

export default nextConfig;
