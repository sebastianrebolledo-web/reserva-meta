"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import Link from "next/link";
import styles from "../styles/AdminDashboard.module.css";

interface AdminDashboardProps {
  token: string;
  adminEmail?: string;
  onLogout: () => void;
}

interface KPI {
  total_solicitudes: number;
  solicitudes_activas: number;
  solicitudes_entregadas: number;
  total_equipos: number;
  en_prestamo: number;
  disponibles: number;
  en_mantenimiento: number;
}

interface Solicitud {
  id: number;
  folio: string;
  applicant_email: string;
  kam_name: string;
  commercial_management: string;
  client_name: string;
  estado: string;
  request_date: string;
  delivery_date: string;
  created_at: string;
}

export default function AdminDashboard({ token, adminEmail, onLogout }: AdminDashboardProps) {
  const [kpis, setKpis] = useState<KPI | null>(null);
  const [solicitudes, setSolicitudes] = useState<Solicitud[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("TODOS");

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [resKpis, resSols] = await Promise.all([
        fetch(`${apiUrl}/api/v1/admin/kpis`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/api/v1/admin/solicitudes`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (!resKpis.ok || !resSols.ok) {
        if (resKpis.status === 401 || resSols.status === 401) {
          onLogout();
          return;
        }
        throw new Error("Error al cargar datos del servidor.");
      }

      const dataKpis = await resKpis.json();
      const dataSols = await resSols.json();

      setKpis(dataKpis);
      setSolicitudes(dataSols);
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || "Error de conexión con el backend.");
    } finally {
      setLoading(false);
    }
  }, [apiUrl, token, onLogout]);

  useEffect(() => {
    let ignore = false;
    async function loadInitial() {
      setError(null);
      try {
        const [resKpis, resSols] = await Promise.all([
          fetch(`${apiUrl}/api/v1/admin/kpis`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`${apiUrl}/api/v1/admin/solicitudes`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

        if (!resKpis.ok || !resSols.ok) {
          if (resKpis.status === 401 || resSols.status === 401) {
            onLogout();
            return;
          }
          throw new Error("Error al cargar datos del servidor.");
        }

        const dataKpis = await resKpis.json();
        const dataSols = await resSols.json();

        if (!ignore) {
          setKpis(dataKpis);
          setSolicitudes(dataSols);
        }
      } catch (err: unknown) {
        if (!ignore) {
          const e = err as Error;
          setError(e.message || "Error de conexión con el backend.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }
    loadInitial();
    return () => {
      ignore = true;
    };
  }, [apiUrl, token, onLogout]);

  const handleUpdateStatus = async (id: number, newStatus: string) => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/admin/solicitudes/${id}/estado`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ estado: newStatus }),
      });
      if (res.ok) {
        fetchData();
      } else {
        alert("No se pudo actualizar el estado de la reserva.");
      }
    } catch {
      alert("Error de conexión al actualizar.");
    }
  };

  const handleDownloadActa = async (id: number, folio: string, clientName: string) => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/admin/solicitudes/${id}/acta`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Error al generar PDF");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Acta_${folio}_${clientName.replace(/\s+/g, "_")}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      alert("Error al descargar el Acta PDF.");
    }
  };

  // Filtered requests
  const filteredSolicitudes = useMemo(() => {
    return solicitudes.filter((sol) => {
      const matchesSearch =
        sol.folio.toLowerCase().includes(searchQuery.toLowerCase()) ||
        sol.kam_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        sol.client_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        sol.applicant_email.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus =
        statusFilter === "TODOS" || sol.estado === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [solicitudes, searchQuery, statusFilter]);

  if (loading) {
    return (
      <div className={styles.loadingState}>
        <div className={styles.spinner} />
        <p>Cargando panel de administración...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.errorState}>
        <p>⚠️ {error}</p>
        <button className={styles.navPortalBtn} onClick={fetchData}>
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerInfo}>
          <div className={styles.badge}>
            <span>● Consola Central de Control TI</span>
          </div>
          <h1 className={styles.title}>Panel de Administración Meta Quest</h1>
          <p className={styles.subtitle}>
            Gestión de inventario de Realidad Virtual, validación de préstamos comerciales y emisión de actas oficiales.
          </p>
        </div>

        <div className={styles.headerActions}>
          {adminEmail && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "6px 14px",
                background: "rgba(56, 189, 248, 0.08)",
                border: "1px solid rgba(56, 189, 248, 0.2)",
                borderRadius: "9999px",
                fontSize: "12px",
                color: "var(--text-secondary)",
              }}
            >
              <span style={{ color: "var(--accent-cyan)", fontSize: "10px" }}>●</span>
              <span>{adminEmail}</span>
            </div>
          )}
          <Link href="/" className={styles.navPortalBtn}>
            <span>←</span>
            <span>Portal de Reservas</span>
          </Link>
          <button className={styles.logoutBtn} onClick={onLogout}>
            Cerrar Sesión
          </button>
        </div>
      </header>

      {/* KPI Cards */}
      {kpis && (
        <div className={styles.kpiGrid}>
          <div className={styles.kpiCard}>
            <div className={styles.kpiHeader}>
              <span className={styles.kpiLabel}>Total Solicitudes</span>
              <span className={styles.kpiIcon}>📋</span>
            </div>
            <div className={styles.kpiValue}>{kpis.total_solicitudes ?? 0}</div>
            <div className={styles.kpiSubtext}>Registradas en base de datos</div>
          </div>

          <div className={styles.kpiCard}>
            <div className={styles.kpiHeader}>
              <span className={styles.kpiLabel}>En Préstamo (Activas)</span>
              <span className={styles.kpiIcon}>🥽</span>
            </div>
            <div className={styles.kpiValue} style={{ color: "var(--accent-cyan)" }}>
              {kpis.solicitudes_activas ?? 0}
            </div>
            <div className={styles.kpiSubtext}>Equipos con clientes</div>
          </div>

          <div className={styles.kpiCard}>
            <div className={styles.kpiHeader}>
              <span className={styles.kpiLabel}>Equipos Disponibles</span>
              <span className={styles.kpiIcon}>🟢</span>
            </div>
            <div className={styles.kpiValue} style={{ color: "#34d399" }}>
              {kpis.disponibles ?? 0}
            </div>
            <div className={styles.kpiSubtext}>Listos para despacho inmediato</div>
          </div>

          <div className={styles.kpiCard}>
            <div className={styles.kpiHeader}>
              <span className={styles.kpiLabel}>Inventario Total</span>
              <span className={styles.kpiIcon}>📦</span>
            </div>
            <div className={styles.kpiValue}>{kpis.total_equipos ?? 0}</div>
            <div className={styles.kpiSubtext}>Visores, mandos y accesorios</div>
          </div>
        </div>
      )}

      {/* Table Content Card */}
      <div className={styles.contentCard}>
        <div className={styles.contentToolbar}>
          <h2 className={styles.contentTitle}>
            <span>Historial y Control de Solicitudes</span>
            <span className={styles.tableCount}>
              {filteredSolicitudes.length}{" "}
              {filteredSolicitudes.length === 1 ? "registro" : "registros"}
            </span>
          </h2>

          <div className={styles.searchFilterWrapper}>
            <input
              type="text"
              placeholder="Buscar por Folio, KAM o Cliente..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={styles.searchInput}
            />

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className={styles.searchInput}
              style={{ minWidth: "150px" }}
            >
              <option value="TODOS">Todos los estados</option>
              <option value="En préstamo">En préstamo</option>
              <option value="Entregado">Entregado</option>
              <option value="Vencido">Vencido</option>
            </select>
          </div>
        </div>

        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Folio</th>
                <th>KAM Responsable</th>
                <th>Cliente Destinatario</th>
                <th>Gerencia</th>
                <th>Fecha Devolución</th>
                <th>Estado</th>
                <th style={{ textAlign: "center" }}>Acta PDF</th>
              </tr>
            </thead>
            <tbody>
              {filteredSolicitudes.map((sol) => (
                <tr key={sol.id}>
                  <td>
                    <span className={styles.folioBadge}>{sol.folio}</span>
                  </td>
                  <td>
                    <div className={styles.kamText}>{sol.kam_name}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                      {sol.applicant_email}
                    </div>
                  </td>
                  <td>
                    <div className={styles.clientText}>{sol.client_name}</div>
                  </td>
                  <td>
                    <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                      {sol.commercial_management}
                    </span>
                  </td>
                  <td>
                    <span className={styles.dateBadge}>
                      📅 {sol.delivery_date}
                    </span>
                  </td>
                  <td>
                    <select
                      value={sol.estado}
                      onChange={(e) => handleUpdateStatus(sol.id, e.target.value)}
                      className={`${styles.statusSelect} ${
                        sol.estado === "En préstamo"
                          ? styles.en_prestamo
                          : sol.estado === "Entregado"
                          ? styles.entregado
                          : styles.vencido
                      }`}
                    >
                      <option value="En préstamo">En préstamo</option>
                      <option value="Entregado">Entregado</option>
                      <option value="Vencido">Vencido</option>
                    </select>
                  </td>
                  <td style={{ textAlign: "center" }}>
                    <button
                      type="button"
                      className={styles.actaBtn}
                      onClick={() => handleDownloadActa(sol.id, sol.folio, sol.client_name)}
                      title="Descargar Acta de Préstamo oficial en PDF"
                    >
                      <span>📥</span>
                      <span>PDF</span>
                    </button>
                  </td>
                </tr>
              ))}

              {filteredSolicitudes.length === 0 && (
                <tr>
                  <td colSpan={7}>
                    <div className={styles.emptyState}>
                      <div className={styles.emptyIcon}>🥽</div>
                      <p>No se encontraron solicitudes con los criterios indicados.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
