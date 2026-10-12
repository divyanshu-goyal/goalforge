import type { Metadata } from "next";
import "./globals.css";
import SessionBootstrap from "./session-bootstrap";

export const metadata: Metadata = {
  title: "GoalForge AI",
  description: "Build a learning path for your programming goals.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body><SessionBootstrap />{children}</body>
    </html>
  );
}
