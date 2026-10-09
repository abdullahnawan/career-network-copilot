import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // The app is opened at 127.0.0.1 so the API's session cookie (set on 127.0.0.1:8000) works.
  // Next 16 blocks dev resources (HMR, client scripts) from hosts other than localhost by default.
  allowedDevOrigins: ["127.0.0.1"],
};

export default nextConfig;
