import { NextResponse } from "next/server";
import { createSolicitud } from "@/lib/store";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const {
      applicant_email,
      kam_name,
      commercial_management,
      client_name,
      request_date,
      duration_days,
      delivery_date,
      equipment_details,
      notes,
    } = body;

    if (!applicant_email || !kam_name || !client_name || !request_date || !duration_days) {
      return NextResponse.json(
        { detail: "Faltan campos obligatorios para registrar la reserva." },
        { status: 400 }
      );
    }

    if (!Array.isArray(equipment_details) || equipment_details.length === 0) {
      return NextResponse.json(
        { detail: "Debes seleccionar al menos un equipo." },
        { status: 400 }
      );
    }

    const sol = createSolicitud({
      applicant_email: applicant_email.trim().toLowerCase(),
      kam_name: kam_name.trim(),
      commercial_management: commercial_management || "Otras",
      client_name: client_name.trim(),
      request_date,
      duration_days: Number(duration_days),
      delivery_date: delivery_date || request_date,
      equipment_details,
      notes: notes || "",
      event_id: `MQ-CAL-${Date.now()}`,
      event_link: "https://calendar.google.com",
    });

    const equipmentSummary = equipment_details
      .map((item: { quantity: number; name: string }) => `${item.quantity}x ${item.name}`)
      .join(", ");

    return NextResponse.json(
      {
        success: true,
        message: "Reserva creada. Acta de Préstamo generada y registrada exitosamente.",
        event_id: sol.event_id,
        event_link: sol.event_link,
        email_notification_sent: true,
        applicant_email: sol.applicant_email,
        kam_name: sol.kam_name,
        client_name: sol.client_name,
        request_date: sol.request_date,
        duration_days: sol.duration_days,
        delivery_date: sol.delivery_date,
        equipment_summary: equipmentSummary,
      },
      { status: 201 }
    );
  } catch (error) {
    return NextResponse.json(
      { detail: "Error creando reserva: " + String(error) },
      { status: 500 }
    );
  }
}
