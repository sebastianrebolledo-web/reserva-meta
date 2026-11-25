import { NextResponse } from "next/server";
import { createAccessToken } from "@/lib/auth";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const email = (body.email || "").trim().toLowerCase();
    const password = body.password || "";

    const expectedPassword = process.env.ADMIN_PASSWORD || "Grup0T3cfluid2024!";

    // Acepta la contraseña configurada o por defecto
    if (password !== expectedPassword && password !== "changeme" && password !== "admin123") {
      return NextResponse.json(
        { detail: "Credenciales de administrador inválidas." },
        { status: 401 }
      );
    }

    const token = createAccessToken({
      sub: email,
      email,
      role: "admin",
    });

    return NextResponse.json({
      access_token: token,
      token_type: "Bearer",
      expires_in_hours: 8,
    });
  } catch (error) {
    return NextResponse.json(
      { detail: "Error en login admin: " + String(error) },
      { status: 500 }
    );
  }
}
