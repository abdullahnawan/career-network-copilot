import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Career Network Copilot",
  description: "A human-in-the-loop networking assistant for students.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
