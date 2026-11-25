"use client";

import React, { useState, useMemo } from "react";
import styles from "../styles/Reservation.module.css";
import EquipmentSelector, { EquipmentSelection } from "./EquipmentSelector";
import CalendarDatePicker from "./CalendarDatePicker";

interface ReservationFormProps {
  userEmail: string;
  authToken?: string;
  onLogout: () => void;
}

const DEFAULT_EQUIPMENT: EquipmentSelection[] = [
  { name: "Visor Meta Quest 3 (128GB)", quantity: 1, selected: true },
  { name: "Controles Touch Plus (Par Izq/Der)", quantity: 1, selected: true },
  { name: "Cable Link USB-C (5 metros)", quantity: 1, selected: false },
  { name: "Cargador Rápido 45W + Cable USB-C", quantity: 1, selected: true },
  { name: "Estuche Rígido de Transporte", quantity: 1, selected: true },
  { name: "Correa Elite Strap con Batería", quantity: 1, selected: false },
];

const COMMERCIAL_MANAGEMENTS = [
  "GC - IHH",
  "GC - FGP",
  "Gerencia Comercial Minería",
  "Gerencia Comercial Celulosa & Papel",
  "Gerencia Comercial Energía & Utilities",
  "Gerencia Comercial Industrial & Alimentos",
  "Gerencia Comercial Proyectos Especiales",
  "Otras",
];

export default function ReservationForm({ userEmail, authToken, onLogout }: ReservationFormProps) {

  // Estado de los campos del formulario
  const [kamName, setKamName] = useState("");
  const [commercialManagement, setCommercialManagement] = useState(COMMERCIAL_MANAGEMENTS[0]);
  const [clientName, setClientName] = useState("");
  
  // Fecha de inicio por defecto: Mañana
  const defaultDate = useMemo(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split("T")[0];
  }, []);

  const [requestDate, setRequestDate] = useState(defaultDate);
  const [durationDays, setDurationDays] = useState<number>(3);
  const [equipmentList, setEquipmentList] = useState<EquipmentSelection[]>(DEFAULT_EQUIPMENT);
  const [notes, setNotes] = useState("");

  // Estado de envío y resultados
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<{
    eventId: string;
    eventLink: string;
    deliveryDate: string;
    client: string;
    summary: string;
  } | null>(null);

  // =========================================================================
  // LÓGICA REACTIVA: Cálculo automático de 'Fecha de Entrega'
  // =========================================================================
  const { calculatedDeliveryDate, formattedDeliveryDate } = useMemo(() => {
    if (!requestDate || !durationDays || durationDays <= 0) {
      return { calculatedDeliveryDate: "", formattedDeliveryDate: "Indica fecha y días válidos" };
    }

    try {
      const parts = requestDate.split("-").map(Number);
      // Año, Mes (0-indexado), Día
      const startDate = new Date(parts[0], parts[1] - 1, parts[2]);
      
      const targetDate = new Date(startDate);
      targetDate.setDate(targetDate.getDate() + Number(durationDays));

      const isoDate = targetDate.toISOString().split("T")[0];

      // Formato amigable en español utilizando Intl nativo del navegador
      const formatter = new Intl.DateTimeFormat("es-CL", {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
      });

      const formatted = formatter.format(targetDate);
      // Capitalizar primer letra del día de semana
      const capitalized = formatted.charAt(0).toUpperCase() + formatted.slice(1);

      return {
        calculatedDeliveryDate: isoDate,
        formattedDeliveryDate: capitalized,
      };
    } catch {
      return { calculatedDeliveryDate: "", formattedDeliveryDate: "Fecha inválida" };
    }
  }, [requestDate, durationDays]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    // Validar que al menos un equipo esté seleccionado
    const selectedItems = equipmentList.filter((item) => item.selected);
    if (selectedItems.length === 0) {
      setErrorMsg("Debes seleccionar al menos un equipo o accesorio para la reserva.");
      return;
    }

    setLoading(true);

    const payload = {
      applicant_email: userEmail,
      kam_name: kamName.trim(),
      commercial_management: commercialManagement,
      client_name: clientName.trim(),
      request_date: requestDate,
      duration_days: Number(durationDays),
      delivery_date: calculatedDeliveryDate,
      equipment_details: selectedItems.map((item) => ({
        name: item.name,
        quantity: item.quantity,
        serial_or_notes: item.serial_or_notes || null,
      })),
      notes: notes.trim() || null,
    };

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";

    try {
      // Uso de fetch nativo conforme a la regla de cero dependencias
      const requestHeaders: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (authToken) {
        requestHeaders["Authorization"] = `Bearer ${authToken}`;
      }

      const response = await fetch(`${apiUrl}/api/v1/reservations`, {
        method: "POST",
        headers: requestHeaders,
        body: JSON.stringify(payload),
      });


      const data = await response.json();

      if (!response.ok) {
        const detail = data?.detail;
        const msg = Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg || "").join(", ")
          : typeof detail === "string"
          ? detail
          : "Error al registrar la solicitud.";
        throw new Error(msg);
      }

      setSuccessData({
        eventId: data.event_id || "",
        eventLink: data.event_link || "https://calendar.google.com",
        deliveryDate: data.delivery_date,
        client: data.client_name,
        summary: data.equipment_summary,
      });
    } catch (err: unknown) {
      const error = err as Error;
      setErrorMsg(error.message || "No fue posible conectar con el servidor backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSuccessData(null);
    setClientName("");
    setNotes("");
    setEquipmentList(DEFAULT_EQUIPMENT);
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.badge}>
          <span>● Conectado a Google Calendar & Gmail</span>
        </div>
        <h1 className={styles.title}>Reserva de Equipos Meta Quest</h1>
        <p className={styles.subtitle}>
          Solicitud oficial de préstamo de visores de Realidad Virtual para demostraciones comerciales con clientes.
        </p>
      </div>

      {/* Barra de usuario activo */}
      <div className={styles.userBar}>
        <div className={styles.userInfo} style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <span className={styles.userDot}></span>
          <span>
            Solicitante: <strong>{userEmail}</strong>
          </span>
          <span
            style={{
              fontSize: "11px",
              background: "rgba(16, 185, 129, 0.15)",
              color: "#34d399",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              padding: "2px 8px",
              borderRadius: "12px",
              fontWeight: 600,
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <span>✓</span>
            <span>Correo Validado</span>
          </span>
        </div>
        <button type="button" onClick={onLogout} className={styles.logoutBtn}>
          Cerrar Sesión
        </button>
      </div>

      {/* Formulario Principal */}
      <div className={styles.formCard}>
        {errorMsg && (
          <div className={styles.alertError}>
            <span>⚠️</span>
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Sección 1: Datos del KAM y Cliente */}
          <div className={styles.sectionTitle}>
            <span>1. Información Comercial</span>
          </div>

          <div className={styles.grid2}>
            <div className={styles.field}>
              <label htmlFor="kam-name" className={styles.label}>
                KAM Responsable *
              </label>
              <input
                id="kam-name"
                type="text"
                placeholder="Ej. Sebastián Rebolledo"
                value={kamName}
                onChange={(e) => setKamName(e.target.value)}
                className={styles.input}
                required
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="comm-mgmt" className={styles.label}>
                Gerencia Comercial *
              </label>
              <select
                id="comm-mgmt"
                value={commercialManagement}
                onChange={(e) => setCommercialManagement(e.target.value)}
                className={styles.select}
                required
              >
                {COMMERCIAL_MANAGEMENTS.map((mgmt) => (
                  <option key={mgmt} value={mgmt}>
                    {mgmt}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className={styles.field}>
            <label htmlFor="client-name" className={styles.label}>
              Cliente Destinatario *
            </label>
            <input
              id="client-name"
              type="text"
              placeholder="Ej. Minera Escondida / CMPC / Celulosa Arauco"
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
              className={styles.input}
              required
            />
          </div>

          {/* Sección 2: Fechas y Lógica Reactiva */}
          <div className={styles.sectionTitle} style={{ marginTop: "32px" }}>
            <span>2. Período de Préstamo y Cálculo de Entrega</span>
          </div>

          <div className={styles.grid2}>
            <div className={styles.field}>
              <label htmlFor="req-date" className={styles.label}>
                Fecha de Solicitud (Inicio) *
              </label>
              <CalendarDatePicker
                id="req-date"
                value={requestDate}
                onChange={setRequestDate}
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="duration-days" className={styles.label}>
                Tiempo de Petición (Días) *
              </label>
              <input
                id="duration-days"
                type="number"
                min="1"
                max="90"
                value={durationDays}
                onChange={(e) => setDurationDays(Math.max(1, parseInt(e.target.value) || 1))}
                className={styles.input}
                required
              />
            </div>
          </div>

          {/* Componente Reactivo Destacado de Fecha de Entrega */}
          <div className={styles.reactiveDateCard}>
            <div className={styles.dateInfo}>
              <span className={styles.dateLabel}>📅 Fecha Calculada de Entrega (Devolución)</span>
              <span className={styles.dateValue}>{formattedDeliveryDate}</span>
            </div>
            <div className={styles.durationTag}>
              {durationDays} {durationDays === 1 ? "día de préstamo" : "días de préstamo"}
            </div>
          </div>

          {/* Sección 3: Equipos Solicitados */}
          <div className={styles.sectionTitle} style={{ marginTop: "32px" }}>
            <span>3. Detalles de los Equipos Meta Quest / Oculus *</span>
          </div>

          <EquipmentSelector items={equipmentList} onChange={setEquipmentList} />

          {/* Sección 4: Observaciones */}
          <div className={styles.field} style={{ marginTop: "16px" }}>
            <label htmlFor="notes" className={styles.label}>
              Observaciones o Requerimientos de Software (Opcional)
            </label>
            <textarea
              id="notes"
              placeholder="Ej. Requiere software de demostración de gemelos digitales precargado o accesorios específicos de seguridad."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className={styles.textarea}
            />
          </div>

          {/* Botón de Envío */}
          <button
            type="submit"
            className={styles.submitBtn}
            disabled={loading || !kamName.trim() || !clientName.trim()}
          >
            {loading ? (
              <span>Procesando y Sincronizando con Google Calendar...</span>
            ) : (
              <span>Confirmar Reserva y Notificar por Gmail</span>
            )}
          </button>
        </form>
      </div>

      {/* Modal de Éxito al Confirmar Reserva */}
      {successData && (
        <div className={styles.modalOverlay}>
          <div className={`${styles.modalContent} animate-fade-in`}>
            <div className={styles.successIcon}>✓</div>
            <h2 className={styles.modalTitle}>¡Reserva Confirmada Exitosamente!</h2>
            <p className={styles.modalText}>
              Se ha creado el evento en Google Calendar y se ha enviado la notificación por correo al solicitante y a Soporte TI.
            </p>

            <div className={styles.modalDetails}>
              <div className={styles.modalDetailRow}>
                <span style={{ color: "var(--text-secondary)" }}>Cliente:</span>
                <span style={{ fontWeight: 600 }}>{successData.client}</span>
              </div>
              <div className={styles.modalDetailRow}>
                <span style={{ color: "var(--text-secondary)" }}>Fecha de Devolución:</span>
                <span style={{ color: "var(--accent-cyan)", fontWeight: 700 }}>
                  {successData.deliveryDate}
                </span>
              </div>
              <div className={styles.modalDetailRow}>
                <span style={{ color: "var(--text-secondary)" }}>Equipos:</span>
                <span style={{ maxWidth: "260px", textAlign: "right" }}>{successData.summary}</span>
              </div>
              <div className={styles.modalDetailRow}>
                <span style={{ color: "var(--text-secondary)" }}>Notificados:</span>
                <span style={{ color: "var(--success)" }}>{userEmail}, soporteti@grupotecfluid.com</span>
              </div>
            </div>

            <div className={styles.modalActions}>
              <a
                href={successData.eventLink}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.modalLinkBtn}
              >
                Abrir en Calendar ↗
              </a>
              <button
                type="button"
                onClick={handleReset}
                className={styles.modalCloseBtn}
              >
                Nueva Solicitud
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
