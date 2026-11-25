export interface EquipmentItem {
  name: string;
  quantity: number;
  serial_or_notes?: string | null;
}

export interface Solicitud {
  id: number;
  folio: string;
  applicant_email: string;
  kam_name: string;
  commercial_management: string;
  client_name: string;
  request_date: string;
  duration_days: number;
  delivery_date: string;
  equipment_details: EquipmentItem[];
  notes?: string;
  event_id?: string;
  event_link?: string;
  estado: "En préstamo" | "Entregado" | "Vencido";
  created_at: string;
}

export interface InventoryItem {
  id: number;
  modelo: string;
  numero_serie: string;
  estado: "Disponible" | "En préstamo" | "En mantenimiento";
}

// Almacén en memoria de inventario y solicitudes
const inventory: InventoryItem[] = [
  { id: 1, modelo: "Kit Meta Quest 3 – Completo #1", numero_serie: "MQ3-KIT-001", estado: "Disponible" },
  { id: 2, modelo: "Kit Meta Quest 3 – Completo #2", numero_serie: "MQ3-KIT-002", estado: "Disponible" },
  { id: 3, modelo: "Kit Meta Quest 3 – Completo #3", numero_serie: "MQ3-KIT-003", estado: "Disponible" },
  { id: 4, modelo: "Kit Meta Quest 3 – Completo #4", numero_serie: "MQ3-KIT-004", estado: "Disponible" },
];

const solicitudes: Solicitud[] = [];
let nextId = 1;

function generateFolio(): string {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  const dateStr = `${yyyy}${mm}${dd}`;
  const countToday = solicitudes.filter((s) => s.folio.startsWith(`MQ-${dateStr}`)).length;
  const num = String(countToday + 1).padStart(4, "0");
  return `MQ-${dateStr}-${num}`;
}

export function createSolicitud(data: Omit<Solicitud, "id" | "folio" | "estado" | "created_at">): Solicitud {
  const folio = generateFolio();
  const created_at = new Date().toISOString();
  const nueva: Solicitud = {
    ...data,
    id: nextId++,
    folio,
    estado: "En préstamo",
    created_at,
  };
  solicitudes.unshift(nueva);
  return nueva;
}

export function getAllSolicitudes(): Solicitud[] {
  const today = new Date().toISOString().split("T")[0];
  return solicitudes.map((sol) => {
    // Si ya pasó la fecha de entrega y sigue 'En préstamo', marcar como 'Vencido'
    if (sol.estado === "En préstamo" && sol.delivery_date < today) {
      return { ...sol, estado: "Vencido" as const };
    }
    return sol;
  });
}

export function getSolicitudById(id: number): Solicitud | null {
  const list = getAllSolicitudes();
  return list.find((s) => s.id === id) || null;
}

export function updateSolicitudEstado(id: number, nuevoEstado: "En préstamo" | "Entregado" | "Vencido"): Solicitud | null {
  const sol = solicitudes.find((s) => s.id === id);
  if (!sol) return null;
  sol.estado = nuevoEstado;
  return sol;
}

export function getKpiSummary() {
  const list = getAllSolicitudes();
  const totalEquipos = inventory.length;
  const solicitudesActivas = list.filter((s) => s.estado === "En préstamo" || s.estado === "Vencido").length;
  const disponibles = Math.max(0, totalEquipos - solicitudesActivas);
  const totalSolicitudes = list.length;
  const solicitudesEntregadas = list.filter((s) => s.estado === "Entregado").length;

  return {
    total_equipos: totalEquipos,
    en_prestamo: solicitudesActivas,
    disponibles,
    en_mantenimiento: 0,
    total_solicitudes: totalSolicitudes,
    solicitudes_activas: solicitudesActivas,
    solicitudes_entregadas: solicitudesEntregadas,
  };
}
