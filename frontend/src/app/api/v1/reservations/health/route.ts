import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "online",
    service: "Sistema de Reserva Meta Quest (Consolidado)",
    corporate_domain: "grupotecfluid.com",
    it_support_emails: ["soporteti@grupotecfluid.com"],
    auth_mode: "integrated",
    features: ["calendar", "gmail", "acta_pdf"],
  });
}
