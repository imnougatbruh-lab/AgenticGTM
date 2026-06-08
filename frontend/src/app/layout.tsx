import type { Metadata } from "next";
import { NextAuthProvider } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Xyroco — The Autonomous Growth Operating System",
  description: "Autonomous directory submissions, copywriting, and B2B growth outreach on autopilot.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <NextAuthProvider>
          {children}
        </NextAuthProvider>
      </body>
    </html>
  );
}