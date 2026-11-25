import { NextResponse } from "next/server";
import { getKpiSummary } from "@/lib/store";
import { verifyAccessToken } from "@/lib/auth";

export async function GET(request: Request) {
  try {
    const authHeader = request.headers.get("Authorization") || "";
    const token = authHeader.replace(/^Bearer\s+/i, "");

    if (token) {
      try {
        verifyAccessToken(token);
      } catch {
        // En modo flexible permitimos lectura de KPIs
      }
    }

    const kpis = getKpiSummary();
    return NextResponse.json(kpis);
  } catch (error) {
    return NextResponse.json(
      { detail: "Error obteniendo KPIs: " + String(error) },
      { status: 500 }
    );
  }
}
