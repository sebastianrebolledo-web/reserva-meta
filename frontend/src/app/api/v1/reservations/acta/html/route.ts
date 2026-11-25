import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const reservation = await request.json();

    const equipmentRows = (reservation.equipment_details || [])
      .map(
        (item: { name: string; quantity: number; serial_or_notes?: string }) => `
        <tr>
          <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0;">${item.name}</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; text-align: center;">${item.quantity}</td>
          <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0;">${item.serial_or_notes || "-"}</td>
        </tr>
      `
      )
      .join("");

    const html = `
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <title>Acta de Préstamo - Meta Quest</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; padding: 32px; color: #1e293b; background: #fff; max-width: 800px; margin: 0 auto; }
        .header { border-bottom: 2px solid #024c80; padding-bottom: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }
        .title { color: #024c80; font-size: 22px; font-weight: 700; margin: 0; }
        .info-table, .equip-table { width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 14px; }
        .info-table td { padding: 6px 12px; }
        .equip-table th { background: #024c80; color: #fff; text-align: left; padding: 8px 14px; font-size: 13px; }
        .footer { margin-top: 48px; display: flex; justify-content: space-between; text-align: center; font-size: 13px; }
        .sign-box { border-top: 1px solid #64748b; width: 40%; padding-top: 8px; }
      </style>
    </head>
    <body>
      <div class="header">
        <div>
          <h1 class="title">ACTA DE PRÉSTAMO DE EQUIPOS VR</h1>
          <p style="margin: 4px 0 0; color: #64748b; font-size: 13px;">Grupo Tecfluid S.A. — División Realidad Virtual</p>
        </div>
      </div>

      <table class="info-table" style="background: #f8fafc; border-radius: 8px;">
        <tr><td><strong>KAM Responsable:</strong></td><td>${reservation.kam_name}</td></tr>
        <tr><td><strong>Gerencia Comercial:</strong></td><td>${reservation.commercial_management}</td></tr>
        <tr><td><strong>Correo Solicitante:</strong></td><td>${reservation.applicant_email}</td></tr>
        <tr><td><strong>Cliente / Destino:</strong></td><td>${reservation.client_name}</td></tr>
        <tr><td><strong>Fecha Solicitud:</strong></td><td>${reservation.request_date}</td></tr>
        <tr><td><strong>Días de Préstamo:</strong></td><td>${reservation.duration_days} días</td></tr>
        <tr><td><strong>Fecha de Devolución:</strong></td><td><strong style="color: #024c80;">${reservation.delivery_date}</strong></td></tr>
      </table>

      <h3>Equipos y Accesorios Entregados</h3>
      <table class="equip-table">
        <thead>
          <tr><th>Descripción del Equipo</th><th style="text-align: center;">Cantidad</th><th>Notas / N° Serie</th></tr>
        </thead>
        <tbody>
          ${equipmentRows}
        </tbody>
      </table>

      ${reservation.notes ? `<p><strong>Observaciones:</strong> ${reservation.notes}</p>` : ""}

      <div class="footer">
        <div class="sign-box">
          Firma y Aprobación TI<br><strong>Soporte TI Tecfluid</strong>
        </div>
        <div class="sign-box">
          Firma Receptor (KAM)<br><strong>${reservation.kam_name}</strong>
        </div>
      </div>
    </body>
    </html>
    `;

    return new Response(html, {
      status: 200,
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  } catch (error) {
    return NextResponse.json(
      { detail: "Error generando acta: " + String(error) },
      { status: 500 }
    );
  }
}
