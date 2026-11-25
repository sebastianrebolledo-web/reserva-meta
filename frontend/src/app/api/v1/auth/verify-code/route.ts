import { NextResponse } from "next/server";
import { verifyUserOtp, createAccessToken } from "@/lib/auth";

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

    const isValid = verifyUserOtp(email, code);
    if (!isValid) {
      return NextResponse.json(
        { detail: "Código incorrecto o expirado. Por favor solicita uno nuevo." },
        { status: 400 }
      );
    }

    const token = createAccessToken({
      sub: email,
      email,
      role: "user",
    });

    return NextResponse.json({
      access_token: token,
      token_type: "Bearer",
      expires_in_hours: 8,
      email,
      role: "user",
    });
  } catch (error) {
    return NextResponse.json(
      { detail: "Error verificando código: " + String(error) },
      { status: 500 }
    );
  }
}
