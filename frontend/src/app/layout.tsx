import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Reserva de Equipos Meta Quest | Grupo Tecfluid",
  description: "Sistema interno de reserva y préstamo de visores Meta Quest / Oculus para KAMs y Gerencias Comerciales.",
};

import VRBackgroundCanvas from "../components/VRBackgroundCanvas";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </head>
      <body>
        <VRBackgroundCanvas />
        {children}
      </body>
    </html>
  );
}
