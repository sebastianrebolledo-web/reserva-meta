import { NextResponse } from "next/server";
import { getAllSolicitudes } from "@/lib/store";

export async function GET() {
  try {
    const list = getAllSolicitudes();
    return NextResponse.json(list);
  } catch (error) {
    return NextResponse.json(
      { detail: "Error obteniendo solicitudes: " + String(error) },
      { status: 500 }
    );
  }
}
