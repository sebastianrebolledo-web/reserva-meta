import { NextResponse } from "next/server";
import { saveUserOtp } from "@/lib/auth";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const email = (body.email || "").trim().toLowerCase();

    if (!email || !email.includes("@")) {
      return NextResponse.json(
        { detail: "Ingresa un correo electrónico corporativo válido." },
        { status: 400 }
      );
    }

    const domain = email.split("@")[1];
    if (domain !== "grupotecfluid.com") {
      return NextResponse.json(
        { detail: "Acceso denegado: Se requiere un correo corporativo @grupotecfluid.com" },
        { status: 403 }
      );
    }

    // Generar código OTP de 6 dígitos
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    saveUserOtp(email, code);

    return NextResponse.json({
      success: true,
      message: `Código de seguridad enviado a tu casilla corporativa (${email})`,
      is_mock: true,
      demo_code: code,
    });
  } catch (error) {
    return NextResponse.json(
      { detail: "Error procesando solicitud de código: " + String(error) },
      { status: 500 }
    );
  }
}
