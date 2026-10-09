import type { Metadata } from "next";
import "@fontsource-variable/instrument-sans/wght.css";
import "@fontsource/instrument-serif/400.css";
import "./globals.css";
import { AuthProvider } from "../components/AuthProvider";

export const metadata: Metadata = {
  title: "Career Network Copilot",
  description: "A human-in-the-loop networking assistant for students.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body><AuthProvider>{children}</AuthProvider></body>
    </html>
  );
}
