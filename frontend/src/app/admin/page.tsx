"use client";

import React, { useState, useSyncExternalStore } from "react";
import Link from "next/link";
import AdminDashboard from "../../components/AdminDashboard";
import VRBackgroundCanvas from "../../components/VRBackgroundCanvas";
import styles from "../../styles/Login.module.css";

const emptySubscribe = () => () => {};

export default function AdminPage() {
  const isClient = useSyncExternalStore(emptySubscribe, () => true, () => false);
  const [token, setToken] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      return window.sessionStorage.getItem("tecfluid_admin_token");
    }
    return null;
  });
  const [authMethod, setAuthMethod] = useState<"gmail" | "password">("gmail");

  // Form states
  const [email, setEmail] = useState<string>(() => {
    if (typeof window !== "undefined") {
      const saved = window.sessionStorage.getItem("tecfluid_admin_email");
      if (saved) return saved;
    }
    return "soporteti@grupotecfluid.com";
  });
  const [password, setPassword] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [step, setStep] = useState<"request" | "verify">("request");

  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";

  // Step 1: Request OTP code via Gmail
  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setLoading(true);

    try {
      const res = await fetch(`${apiUrl}/api/v1/admin/request-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Error al solicitar código a Gmail");
      }

      const realSend = !data.is_mock;
      const successMsg = realSend
        ? `✉️ Código enviado a tu bandeja de Gmail (${email}). Revisa tu correo y pega el código de 6 dígitos.`
        : `[DEMO] Código generado en modo simulación: ${data.demo_code}`;
      setMessage(successMsg);
      if (data.demo_code) {
        setOtpCode(data.demo_code);
      }
      setStep("verify");
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || "No fue posible conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP code from Gmail
  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch(`${apiUrl}/api/v1/admin/verify-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), code: otpCode.trim() }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Código incorrecto o expirado");
      }

      setToken(data.access_token);
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem("tecfluid_admin_token", data.access_token);
        window.sessionStorage.setItem("tecfluid_admin_email", email.trim());
      }
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || "Error al verificar código.");
    } finally {
      setLoading(false);
    }
  };

  // Password fallback login
  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch(`${apiUrl}/api/v1/admin/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Credenciales incorrectas.");
      }

      setToken(data.access_token);
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem("tecfluid_admin_token", data.access_token);
        window.sessionStorage.setItem("tecfluid_admin_email", email.trim());
      }
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || "Error al iniciar sesión.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setStep("request");
    setOtpCode("");
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem("tecfluid_admin_token");
      window.sessionStorage.removeItem("tecfluid_admin_email");
    }
  };

  if (!isClient) return null;

  // ─── Authenticated: show full dashboard ───────────────────────────────────
  if (token) {
    return (
      <>
        <VRBackgroundCanvas />
        <AdminDashboard token={token} adminEmail={email} onLogout={handleLogout} />
      </>
    );
  }

  // ─── Unauthenticated: show login form ─────────────────────────────────────
  return (
    <>
      <VRBackgroundCanvas />
      <div className={styles.wrapper}>
        <div className={`${styles.card} animate-fade-in`}>
          <div className={styles.logoBadge}>
            <span>Tecfluid VR Hub — Admin</span>
          </div>

          <h1 className={styles.title}>Panel de Administración</h1>
          <p className={styles.subtitle}>
            Control central de visores Meta Quest, inventario y aprobación de actas oficiales.
          </p>

          {/* Method selector tabs */}
          <div
            style={{
              display: "flex",
              gap: "8px",
              background: "rgba(15, 23, 42, 0.6)",
              padding: "4px",
              borderRadius: "8px",
              marginBottom: "20px",
              border: "1px solid rgba(255, 255, 255, 0.08)",
            }}
          >
            <button
              type="button"
              onClick={() => {
                setAuthMethod("gmail");
                setError(null);
                setMessage(null);
              }}
              style={{
                flex: 1,
                padding: "8px 12px",
                borderRadius: "6px",
                border: "none",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
                background:
                  authMethod === "gmail"
                    ? "linear-gradient(135deg, #0284c7, #38bdf8)"
                    : "transparent",
                color: authMethod === "gmail" ? "#ffffff" : "#94a3b8",
                transition: "all 0.2s",
              }}
            >
              ✉️ Acceso con Gmail
            </button>
            <button
              type="button"
              onClick={() => {
                setAuthMethod("password");
                setError(null);
                setMessage(null);
              }}
              style={{
                flex: 1,
                padding: "8px 12px",
                borderRadius: "6px",
                border: "none",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
                background:
                  authMethod === "password"
                    ? "linear-gradient(135deg, #0284c7, #38bdf8)"
                    : "transparent",
                color: authMethod === "password" ? "#ffffff" : "#94a3b8",
                transition: "all 0.2s",
              }}
            >
              🔑 Contraseña Maestra
            </button>
          </div>

          {/* FEEDBACK MESSAGES */}
          {message && (
            <div
              style={{
                background: "rgba(16, 185, 129, 0.12)",
                border: "1px solid rgba(16, 185, 129, 0.3)",
                color: "#34d399",
                padding: "10px 14px",
                borderRadius: "8px",
                fontSize: "13px",
                marginBottom: "16px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span>✓</span>
              <span>{message}</span>
            </div>
          )}

          {error && (
            <div className={styles.errorText} style={{ marginBottom: "16px" }}>
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {/* METHOD 1: GMAIL AUTHENTICATION */}
          {authMethod === "gmail" && (
            <>
              {step === "request" ? (
                <form onSubmit={handleRequestCode} className={styles.form}>
                  <div>
                    <label htmlFor="admin-email" className={styles.label}>
                      Correo Gmail de Soporte TI
                    </label>
                    <div className={styles.inputGroup} style={{ marginTop: "6px" }}>
                      <input
                        id="admin-email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="soporteti@grupotecfluid.com"
                        className={styles.input}
                        required
                        autoFocus
                      />
                    </div>
                    <p
                      style={{
                        fontSize: "12px",
                        color: "var(--text-muted)",
                        marginTop: "6px",
                      }}
                    >
                      Se enviará un código de verificación seguro de 6 dígitos a tu bandeja de entrada de Gmail.
                    </p>
                  </div>

                  <button
                    type="submit"
                    className={styles.submitBtn}
                    disabled={!email.trim() || loading}
                    style={{ marginTop: "16px" }}
                  >
                    <span>{loading ? "Enviando a Gmail..." : "Enviar Código a mi Gmail"}</span>
                    <span>✉️</span>
                  </button>
                </form>
              ) : (
                <form onSubmit={handleVerifyCode} className={styles.form}>
                  <div>
                    <label htmlFor="admin-otp" className={styles.label}>
                      Código de Seguridad (6 dígitos)
                    </label>
                    <div className={styles.inputGroup} style={{ marginTop: "6px" }}>
                      <input
                        id="admin-otp"
                        type="text"
                        maxLength={6}
                        value={otpCode}
                        onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ""))}
                        placeholder="123456"
                        className={styles.input}
                        style={{
                          letterSpacing: "6px",
                          fontSize: "20px",
                          textAlign: "center",
                          fontWeight: 700,
                          fontFamily: "monospace",
                        }}
                        required
                        autoFocus
                      />
                    </div>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginTop: "8px",
                        fontSize: "12px",
                      }}
                    >
                      <span style={{ color: "var(--text-muted)" }}>Enviado a {email}</span>
                      <button
                        type="button"
                        onClick={() => setStep("request")}
                        style={{
                          background: "none",
                          border: "none",
                          color: "var(--accent-cyan)",
                          cursor: "pointer",
                          fontWeight: 600,
                        }}
                      >
                        Reenviar o cambiar correo
                      </button>
                    </div>
                  </div>

                  <button
                    type="submit"
                    className={styles.submitBtn}
                    disabled={otpCode.length < 6 || loading}
                    style={{ marginTop: "16px" }}
                  >
                    <span>{loading ? "Verificando..." : "Ingresar al Panel"}</span>
                    <span>→</span>
                  </button>
                </form>
              )}
            </>
          )}

          {/* METHOD 2: PASSWORD FALLBACK */}
          {authMethod === "password" && (
            <form onSubmit={handlePasswordLogin} className={styles.form}>
              <div>
                <label htmlFor="admin-email-pwd" className={styles.label}>
                  Correo Administrador
                </label>
                <div className={styles.inputGroup} style={{ marginTop: "6px" }}>
                  <input
                    id="admin-email-pwd"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={styles.input}
                    required
                  />
                </div>
              </div>

              <div style={{ marginTop: "14px" }}>
                <label htmlFor="admin-password" className={styles.label}>
                  Contraseña Maestra
                </label>
                <div className={styles.inputGroup} style={{ marginTop: "6px" }}>
                  <input
                    id="admin-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={styles.input}
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                className={styles.submitBtn}
                disabled={!email || !password || loading}
                style={{ marginTop: "20px" }}
              >
                <span>{loading ? "Ingresando..." : "Ingresar con Clave"}</span>
                <span>→</span>
              </button>
            </form>
          )}

          <p className={styles.footerNote} style={{ marginTop: "24px" }}>
            <Link
              href="/"
              style={{
                color: "var(--accent-cyan)",
                textDecoration: "none",
                fontWeight: 600,
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <span>←</span>
              <span>Volver al Portal de Reservas</span>
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
