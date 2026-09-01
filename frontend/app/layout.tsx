import type { Metadata } from "next";

import { Footer } from "@/components/Footer";
import { Navbar } from "@/components/Navbar";

import "./globals.css";

export const metadata: Metadata = {
  title: "AI News Credibility & Misinformation Detection Platform",
  description: "ML-based news credibility analysis, explainability, monitoring, and human review.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col antialiased">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
