import { NextResponse } from "next/server";
import { saveAdminOtp } from "@/lib/auth";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const email = (body.email || "").trim().toLowerCase();

    // Administradores permitidos
    const allowedAdmins = ["soporteti@grupotecfluid.com", "sebastian.rebolledo@grupotecfluid.com"];
    if (!allowedAdmins.includes(email) && !email.endsWith("@grupotecfluid.com")) {
      return NextResponse.json(
        { detail: "Este correo no tiene permisos de administrador." },
        { status: 403 }
      );
    }

    const code = Math.floor(100000 + Math.random() * 900000).toString();
    saveAdminOtp(email, code);

    return NextResponse.json({
      success: true,
      message: `Código enviado exitosamente a tu cuenta (${email})`,
      is_mock: true,
      demo_code: code,
    });
  } catch (error) {
    return NextResponse.json(
      { detail: "Error solicitando código admin: " + String(error) },
      { status: 500 }
    );
  }
}
