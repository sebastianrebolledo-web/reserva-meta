import { NextResponse } from "next/server";
import { updateSolicitudEstado } from "@/lib/store";

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const numId = parseInt(id, 10);
    const body = await request.json();
    const nuevoEstado = body.estado;

    if (!["En préstamo", "Entregado", "Vencido"].includes(nuevoEstado)) {
      return NextResponse.json(
        { detail: "Estado inválido. Opciones: En préstamo, Entregado, Vencido" },
        { status: 400 }
      );
    }

    const updated = updateSolicitudEstado(numId, nuevoEstado);
    if (!updated) {
      return NextResponse.json(
        { detail: "Solicitud no encontrada." },
        { status: 404 }
      );
    }

    return NextResponse.json(updated);
  } catch (error) {
    return NextResponse.json(
      { detail: "Error actualizando estado: " + String(error) },
      { status: 500 }
    );
  }
}
