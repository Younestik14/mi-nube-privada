import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "REBT Suite — Instalaciones Eléctricas",
  description: "Plataforma de diseño y cálculo de instalaciones eléctricas REBT + IEC",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
