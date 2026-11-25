import io
from datetime import date
from typing import List, Dict, Any
from app.schemas.reservation import ReservationCreate

# ReportLab imports
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

PRIMARY_BLUE = colors.HexColor("#024c80")
LIGHT_BLUE_BG = colors.HexColor("#f0f6fb")
BORDER_GRAY = colors.HexColor("#d1d5db")
TEXT_DARK = colors.HexColor("#1e293b")
TEXT_MUTED = colors.HexColor("#64748b")


def get_standard_equipment_rows(reservation: ReservationCreate) -> List[Dict[str, Any]]:
    """
    Retorna la lista de elementos para el acta.
    Incluye el kit estándar de la plantilla institucional y agrega los accesorios extra solicitados.
    """
    base_kit = [
        {"quantity": 1, "description": "Visor Meta Quest 3."},
        {"quantity": 2, "description": "Controles."},
        {"quantity": 1, "description": "Cable de carga."},
        {"quantity": 4, "description": "Pila Duracell recargable."},
        {"quantity": 1, "description": "Adaptador de carga (con adaptador de enchufe americano)."},
        {"quantity": 1, "description": "Cargador para pilas Duracell."},
        {"quantity": 1, "description": "Maletín para visor."},
    ]

    # Identificar ítems extra en la reserva que no están en el kit base
    extra_items = []
    base_names_lower = [item["description"].lower() for item in base_kit]

    for eq in reservation.equipment_details:
        eq_name_lower = eq.name.lower()
        # Si no es visor ni control ni cargador ya contemplado, agregarlo como ítem extra
        is_already_covered = any(
            ("visor" in eq_name_lower and "visor" in b) or
            ("control" in eq_name_lower and "control" in b) or
            ("malet" in eq_name_lower and "malet" in b)
            for b in base_names_lower
        )
        if not is_already_covered:
            extra_items.append({
                "quantity": eq.quantity,
                "description": f"{eq.name}" + (f" ({eq.serial_or_notes})" if eq.serial_or_notes else ".")
            })

    return base_kit + extra_items


def generate_acta_html(reservation: ReservationCreate) -> str:
    """
    Genera el HTML del Acta de Préstamo con un diseño pixel-perfect respecto
    a la plantilla institucional, optimizado para visualización web e impresión PDF.
    """
    rows = get_standard_equipment_rows(reservation)

    req_date_str = reservation.request_date.strftime("%d/%m/%Y")
    delivery_date_str = reservation.delivery_date.strftime("%d/%m/%Y")

    table_rows_html = "".join(
        f"""
        <tr>
          <td class="col-qty">{row['quantity']}</td>
          <td class="col-desc">{row['description']}</td>
          <td class="col-check"><span class="box"></span></td>
          <td class="col-check"><span class="box"></span></td>
        </tr>
        """
        for row in rows
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Acta de Préstamo - Meta Quest</title>
  <style>
    @page {{
      size: letter;
      margin: 18mm 20mm;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      color: #1e293b;
    }}
    body {{
      background-color: #ffffff;
      padding: 24px;
      display: flex;
      justify-content: center;
    }}
    .acta-page {{
      width: 100%;
      max-width: 760px;
      background: #ffffff;
    }}
    /* Header */
    .header-table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 8px;
    }}
    .header-logo-cell {{
      vertical-align: middle;
      width: 45%;
    }}
    .logo-container {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .logo-text {{
      line-height: 1.1;
    }}
    .logo-grupo {{
      font-size: 15px;
      font-weight: 400;
      color: #034982;
      display: block;
      letter-spacing: -0.2px;
    }}
    .logo-tecfluid {{
      font-size: 24px;
      font-weight: 800;
      color: #024c80;
      display: block;
      letter-spacing: -0.5px;
    }}
    .header-title-cell {{
      text-align: right;
      vertical-align: middle;
      width: 55%;
    }}
    .acta-title {{
      font-size: 20px;
      font-weight: 900;
      color: #024c80;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
    }}
    .acta-subtitle {{
      font-size: 13px;
      color: #0369a1;
      font-weight: 500;
    }}
    .divider-blue {{
      height: 3px;
      background: #024c80;
      border: none;
      margin-bottom: 22px;
    }}
    /* Sections */
    .section-title {{
      font-size: 13px;
      font-weight: 800;
      color: #024c80;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      margin-bottom: 12px;
    }}
    /* Solicitante Form */
    .form-section {{
      margin-bottom: 22px;
      font-size: 13px;
    }}
    .form-row {{
      display: flex;
      align-items: flex-end;
      margin-bottom: 10px;
      line-height: 1.4;
    }}
    .form-label {{
      font-weight: 700;
      color: #1e293b;
      white-space: nowrap;
      margin-right: 6px;
    }}
    .form-value-line {{
      flex: 1;
      border-bottom: 1px solid #1e293b;
      padding-bottom: 2px;
      color: #0f172a;
      font-weight: 600;
    }}
    .form-cols {{
      display: flex;
      gap: 20px;
      margin-bottom: 10px;
    }}
    .form-col {{
      flex: 1;
      display: flex;
      align-items: flex-end;
    }}
    /* Table */
    .elements-table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 22px;
      font-size: 12px;
    }}
    .elements-table th {{
      background-color: #f0f6fb;
      color: #024c80;
      font-weight: 700;
      border: 1px solid #cbd5e1;
      padding: 7px 10px;
      text-align: left;
    }}
    .elements-table th.col-qty,
    .elements-table th.col-check {{
      text-align: center;
    }}
    .elements-table td {{
      border: 1px solid #cbd5e1;
      padding: 6px 10px;
      color: #334155;
    }}
    .col-qty {{
      width: 12%;
      text-align: center;
      font-weight: 600;
    }}
    .col-desc {{
      width: 58%;
    }}
    .col-check {{
      width: 15%;
      text-align: center;
    }}
    .box {{
      display: inline-block;
      width: 15px;
      height: 15px;
      border: 1.5px solid #94a3b8;
      border-radius: 2px;
    }}
    /* Terminos */
    .terms-box {{
      background-color: #f8fafc;
      border-left: 4px solid #024c80;
      padding: 12px 16px;
      margin-bottom: 24px;
      font-size: 12px;
      line-height: 1.5;
      color: #334155;
    }}
    /* Firmas */
    .firmas-container {{
      margin-bottom: 28px;
    }}
    .sub-section-title {{
      font-size: 12px;
      font-weight: 800;
      color: #024c80;
      margin-bottom: 2px;
    }}
    .sub-section-desc {{
      font-size: 10.5px;
      color: #64748b;
      font-style: italic;
      margin-bottom: 34px;
    }}
    .signature-grid {{
      display: flex;
      justify-content: space-between;
      gap: 40px;
      margin-bottom: 22px;
    }}
    .signature-block {{
      flex: 1;
      text-align: center;
    }}
    .signature-line {{
      border-top: 1px solid #334155;
      padding-top: 5px;
      font-size: 11px;
      font-weight: 700;
      color: #1e293b;
    }}
    /* Footer */
    .acta-footer {{
      text-align: center;
      font-size: 11px;
      color: #64748b;
      line-height: 1.4;
      border-top: 1px solid #e2e8f0;
      padding-top: 14px;
      margin-top: 10px;
    }}
    .company-name {{
      font-weight: 700;
      color: #334155;
    }}
  </style>
</head>
<body>
  <div class="acta-page">
    <!-- Header -->
    <table class="header-table">
      <tr>
        <td class="header-logo-cell">
          <div class="logo-container">
            <svg width="44" height="44" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M50 10C27.9 10 10 27.9 10 50C10 72.1 27.9 90 50 90C72.1 90 90 72.1 90 50" stroke="#024c80" stroke-width="10" stroke-linecap="round"/>
              <path d="M50 24C35.6 24 24 35.6 24 50C24 64.4 35.6 76 50 76C64.4 76 76 64.4 76 50" stroke="#0284c7" stroke-width="8" stroke-linecap="round"/>
              <circle cx="50" cy="50" r="12" fill="#38bdf8"/>
            </svg>
            <div class="logo-text">
              <span class="logo-grupo">grupo</span>
              <span class="logo-tecfluid">tecfluid</span>
            </div>
          </div>
        </td>
        <td class="header-title-cell">
          <div class="acta-title">ACTA DE PRÉSTAMO</div>
          <div class="acta-subtitle">Solicitud de equipamiento Meta Quest</div>
        </td>
      </tr>
    </table>

    <hr class="divider-blue">

    <!-- 1. DATOS DEL SOLICITANTE -->
    <div class="section-title">1. DATOS DEL SOLICITANTE</div>
    <div class="form-section">
      <div class="form-row">
        <span class="form-label">Nombre del colaborador:</span>
        <span class="form-value-line">{reservation.kam_name}</span>
      </div>

      <div class="form-cols">
        <div class="form-col">
          <span class="form-label">Gerencia / Depto:</span>
          <span class="form-value-line">{reservation.commercial_management}</span>
        </div>
        <div class="form-col">
          <span class="form-label">Cargo:</span>
          <span class="form-value-line">Key Account Manager (KAM)</span>
        </div>
      </div>

      <div class="form-cols">
        <div class="form-col">
          <span class="form-label">Fecha de entrega:</span>
          <span class="form-value-line">{req_date_str}</span>
        </div>
        <div class="form-col">
          <span class="form-label">Fecha de devolución:</span>
          <span class="form-value-line">{delivery_date_str}</span>
        </div>
      </div>

      <div class="form-row" style="margin-top: 4px;">
        <span class="form-label">Cliente / Actividad:</span>
        <span class="form-value-line">{reservation.client_name} ({reservation.duration_days} días de préstamo)</span>
      </div>
    </div>

    <!-- 2. DETALLE DE ELEMENTOS -->
    <div class="section-title">2. DETALLE DE ELEMENTOS</div>
    <table class="elements-table">
      <thead>
        <tr>
          <th class="col-qty">Cantidad</th>
          <th class="col-desc">Descripción</th>
          <th class="col-check">Entrega</th>
          <th class="col-check">Devolución</th>
        </tr>
      </thead>
      <tbody>
        {table_rows_html}
      </tbody>
    </table>

    <!-- 3. TÉRMINOS Y CONDICIONES -->
    <div class="section-title">3. TÉRMINOS Y CONDICIONES</div>
    <div class="terms-box">
      Los equipos entregados deben ser usados exclusivamente por el usuario designado y sus respectivos clientes para la muestra del Showroom virtual Tecfluid Solutions. El colaborador se hace responsable del cuidado, protección y buen uso de los equipos en préstamo desde el momento de su recepción hasta su devolución física.
    </div>

    <!-- 4. REGISTRO DE FIRMAS -->
    <div class="section-title">4. REGISTRO DE FIRMAS</div>
    <div class="firmas-container">
      <div class="sub-section-title">A. ENTREGA</div>
      <div class="sub-section-desc">(Certifica la recepción conforme de los equipos detallados previamente)</div>
      <div class="signature-grid">
        <div class="signature-block">
          <div class="signature-line">Nombre y firma de miembro DP&P</div>
        </div>
        <div class="signature-block">
          <div class="signature-line">Nombre y firma de colaborador</div>
        </div>
      </div>

      <div class="sub-section-title" style="margin-top: 14px;">B. DEVOLUCIÓN</div>
      <div class="sub-section-desc">(Certifica que los equipos fueron devueltos a la empresa en las mismas condiciones)</div>
      <div class="signature-grid">
        <div class="signature-block">
          <div class="signature-line">Nombre y firma de miembro DP&P</div>
        </div>
        <div class="signature-block">
          <div class="signature-line">Nombre y firma de colaborador</div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="acta-footer">
      <div class="company-name">Grupo Tecfluid S.A.</div>
      <div>Avenida La Montaña 58, Colina, Santiago, Chile.</div>
    </div>
  </div>
</body>
</html>
"""


def generate_acta_pdf(reservation: ReservationCreate) -> bytes:
    """
    Genera el archivo binario PDF del Acta de Préstamo usando ReportLab,
    reproduciendo exactamente el formato visual de la plantilla oficial.
    """
    buffer = io.BytesIO()

    # Tamaño carta con márgenes de 36pt (0.5 pulgadas)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=28,
    )

    styles = getSampleStyleSheet()

    # Estilos de párrafo personalizados
    title_style = ParagraphStyle(
        "ActaTitle",
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=PRIMARY_BLUE,
        alignment=TA_RIGHT,
    )

    subtitle_style = ParagraphStyle(
        "ActaSubtitle",
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0369a1"),
        alignment=TA_RIGHT,
    )

    logo_text_grupo = ParagraphStyle(
        "LogoGrupo",
        fontName="Helvetica",
        fontSize=11,
        leading=13,
        textColor=PRIMARY_BLUE,
    )

    logo_text_tecfluid = ParagraphStyle(
        "LogoTecfluid",
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=20,
        textColor=PRIMARY_BLUE,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=PRIMARY_BLUE,
        spaceAfter=6,
    )

    field_label_style = ParagraphStyle(
        "FieldLabel",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=TEXT_DARK,
    )

    field_val_style = ParagraphStyle(
        "FieldVal",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=TEXT_DARK,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=PRIMARY_BLUE,
        alignment=TA_CENTER,
    )

    table_header_left = ParagraphStyle(
        "TableHeaderLeft",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=PRIMARY_BLUE,
        alignment=TA_LEFT,
    )

    table_cell_center = ParagraphStyle(
        "TableCellCenter",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=TEXT_DARK,
        alignment=TA_CENTER,
    )

    table_cell_left = ParagraphStyle(
        "TableCellLeft",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=TEXT_DARK,
        alignment=TA_LEFT,
    )

    terms_style = ParagraphStyle(
        "TermsText",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#334155"),
    )

    firmas_sub = ParagraphStyle(
        "FirmasSub",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=PRIMARY_BLUE,
    )

    firmas_legend = ParagraphStyle(
        "FirmasLegend",
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=TEXT_MUTED,
    )

    firmas_line_text = ParagraphStyle(
        "FirmasLineText",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=TEXT_DARK,
        alignment=TA_CENTER,
    )

    footer_style = ParagraphStyle(
        "FooterText",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=TEXT_MUTED,
        alignment=TA_CENTER,
    )

    story = []

    # 1. HEADER (Logo a la izquierda, Título a la derecha)
    logo_flowable = [
        Paragraph("grupo", logo_text_grupo),
        Paragraph("tecfluid", logo_text_tecfluid),
    ]

    title_flowable = [
        Paragraph("ACTA DE PRÉSTAMO", title_style),
        Paragraph("Solicitud de equipamiento Meta Quest", subtitle_style),
    ]

    header_table = Table(
        [[logo_flowable, title_flowable]],
        colWidths=[250, 290],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))

    # Línea horizontal azul
    story.append(HRFlowable(width="100%", thickness=2.5, color=PRIMARY_BLUE, spaceAfter=14))

    # 2. SECCIÓN 1: DATOS DEL SOLICITANTE
    story.append(Paragraph("1. DATOS DEL SOLICITANTE", section_heading))

    req_date_str = reservation.request_date.strftime("%d/%m/%Y")
    delivery_date_str = reservation.delivery_date.strftime("%d/%m/%Y")

    solicitante_data = [
        [
            Paragraph("Nombre del colaborador:", field_label_style),
            Paragraph(reservation.kam_name, field_val_style),
            "",
            ""
        ],
        [
            Paragraph("Gerencia / Depto:", field_label_style),
            Paragraph(reservation.commercial_management, field_val_style),
            Paragraph("Cargo:", field_label_style),
            Paragraph("Key Account Manager (KAM)", field_val_style),
        ],
        [
            Paragraph("Fecha de entrega:", field_label_style),
            Paragraph(req_date_str, field_val_style),
            Paragraph("Fecha de devolución:", field_label_style),
            Paragraph(delivery_date_str, field_val_style),
        ],
        [
            Paragraph("Cliente / Proyecto:", field_label_style),
            Paragraph(f"{reservation.client_name} ({reservation.duration_days} días de préstamo)", field_val_style),
            "",
            ""
        ],
    ]

    solicitante_table = Table(
        solicitante_data,
        colWidths=[120, 160, 110, 150],
        rowHeights=[18, 18, 18, 18],
    )
    solicitante_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        # Línea inferior subrayada para cada valor
        ("LINEBELOW", (1, 0), (1, 0), 0.75, TEXT_DARK),
        ("LINEBELOW", (1, 1), (1, 1), 0.75, TEXT_DARK),
        ("LINEBELOW", (3, 1), (3, 1), 0.75, TEXT_DARK),
        ("LINEBELOW", (1, 2), (1, 2), 0.75, TEXT_DARK),
        ("LINEBELOW", (3, 2), (3, 2), 0.75, TEXT_DARK),
        ("LINEBELOW", (1, 3), (1, 3), 0.75, TEXT_DARK),
    ]))
    story.append(solicitante_table)
    story.append(Spacer(1, 14))

    # 3. SECCIÓN 2: DETALLE DE ELEMENTOS
    story.append(Paragraph("2. DETALLE DE ELEMENTOS", section_heading))

    table_data = [
        [
            Paragraph("Cantidad", table_header_style),
            Paragraph("Descripción", table_header_left),
            Paragraph("Entrega", table_header_style),
            Paragraph("Devolución", table_header_style),
        ]
    ]

    items = get_standard_equipment_rows(reservation)
    for it in items:
        table_data.append([
            Paragraph(str(it["quantity"]), table_cell_center),
            Paragraph(it["description"], table_cell_left),
            Paragraph("&#9633;", table_cell_center),  # Cuadrado vacío
            Paragraph("&#9633;", table_cell_center),
        ])

    elem_table = Table(
        table_data,
        colWidths=[65, 315, 80, 80],
    )
    elem_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(elem_table)
    story.append(Spacer(1, 12))

    # 4. SECCIÓN 3: TÉRMINOS Y CONDICIONES
    story.append(Paragraph("3. TÉRMINOS Y CONDICIONES", section_heading))

    terms_text = (
        "Los equipos entregados deben ser usados exclusivamente por el usuario designado y sus respectivos "
        "clientes para la muestra del <b>Showroom virtual Tecfluid Solutions</b>. El colaborador se hace "
        "responsable del cuidado, protección y buen uso de los equipos en préstamo desde el momento de su "
        "recepción hasta su devolución física."
    )
    terms_table = Table(
        [[Paragraph(terms_text, terms_style)]],
        colWidths=[540],
    )
    terms_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("LINEBEFORE", (0, 0), (0, -1), 3, PRIMARY_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(terms_table)
    story.append(Spacer(1, 12))

    # 5. SECCIÓN 4: REGISTRO DE FIRMAS
    firmas_story = []
    firmas_story.append(Paragraph("4. REGISTRO DE FIRMAS", section_heading))

    firmas_story.append(Paragraph("A. ENTREGA", firmas_sub))
    firmas_story.append(Paragraph("(Certifica la recepción conforme de los equipos detallados previamente)", firmas_legend))
    firmas_story.append(Spacer(1, 24))

    firmas_a_table = Table(
        [[
            Paragraph("Nombre y firma de miembro DP&P", firmas_line_text),
            "",
            Paragraph("Nombre y firma de colaborador", firmas_line_text),
        ]],
        colWidths=[240, 60, 240],
    )
    firmas_a_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (0, 0), 0.75, TEXT_DARK),
        ("LINEABOVE", (2, 0), (2, 0), 0.75, TEXT_DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    firmas_story.append(firmas_a_table)
    firmas_story.append(Spacer(1, 10))

    firmas_story.append(Paragraph("B. DEVOLUCIÓN", firmas_sub))
    firmas_story.append(Paragraph("(Certifica que los equipos fueron devueltos a la empresa en las mismas condiciones)", firmas_legend))
    firmas_story.append(Spacer(1, 24))

    firmas_b_table = Table(
        [[
            Paragraph("Nombre y firma de miembro DP&P", firmas_line_text),
            "",
            Paragraph("Nombre y firma de colaborador", firmas_line_text),
        ]],
        colWidths=[240, 60, 240],
    )
    firmas_b_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (0, 0), 0.75, TEXT_DARK),
        ("LINEABOVE", (2, 0), (2, 0), 0.75, TEXT_DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    firmas_story.append(firmas_b_table)
    firmas_story.append(Spacer(1, 14))

    # FOOTER
    footer_text = "<b>Grupo Tecfluid S.A.</b><br/>Avenida La Montaña 58, Colina, Santiago, Chile."
    firmas_story.append(Paragraph(footer_text, footer_style))

    story.append(KeepTogether(firmas_story))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
