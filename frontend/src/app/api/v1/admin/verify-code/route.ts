import { NextResponse } from "next/server";
import { verifyAdminOtp, createAccessToken } from "@/lib/auth";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const email = (body.email || "").trim().toLowerCase();
    const code = (body.code || "").trim();

    if (!email || !code) {
      return NextResponse.json(
        { detail: "Correo y código son obligatorios." },
        { status: 400 }
      );
    }

    const isValid = verifyAdminOtp(email, code);
    if (!isValid) {
      return NextResponse.json(
        { detail: "El código ingresado es incorrecto o ha expirado." },
        { status: 400 }
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
      { detail: "Error verificando código admin: " + String(error) },
      { status: 500 }
    );
  }
}
