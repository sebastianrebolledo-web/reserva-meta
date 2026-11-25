"use client";

import React, { useState } from "react";
import styles from "../styles/Login.module.css";

interface CorporateLoginProps {
  onLogin: (email: string, token: string) => void;
  requiredDomain?: string;
}

export default function CorporateLogin({
  onLogin,
  requiredDomain = "grupotecfluid.com",
}: CorporateLoginProps) {
  const [step, setStep] = useState<"request" | "verify">("request");
  const [email, setEmail] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";

  // Paso 1: Solicitar código OTP al correo corporativo
  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    const cleanEmail = email.trim().toLowerCase();

    // Validación general de formato
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(cleanEmail)) {
      setError("Por favor, ingresa una dirección de correo válida.");
      return;
    }

    // Validación estricta de dominio corporativo
    const domain = cleanEmail.split("@")[1];
    if (domain !== requiredDomain.toLowerCase()) {
      setError(`Acceso restringido: Solo se permiten correos corporativos @${requiredDomain}`);
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/request-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: cleanEmail }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Error al solicitar código de verificación.");
      }

      const realSend = !data.is_mock;
      const successMsg = realSend
        ? `✉️ Código de 6 dígitos enviado a tu correo corporativo (${cleanEmail}). Revisa tu bandeja de entrada o spam.`
        : `[MODO PRUEBA] Código simulado generado: ${data.demo_code}`;

      setMessage(successMsg);
      if (data.demo_code) {
        setOtpCode(data.demo_code);
      }
      setStep("verify");
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || "No fue posible conectar con el servidor backend.");
    } finally {
      setLoading(false);
    }
  };

  // Paso 2: Verificar código e ingresar con token Bearer
  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const cleanEmail = email.trim().toLowerCase();

    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/verify-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: cleanEmail,
          code: otpCode.trim(),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Código incorrecto o expirado.");
      }

      onLogin(cleanEmail, data.access_token);
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || "Error al verificar código.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStep("request");
    setOtpCode("");
    setMessage(null);
    setError(null);
  };

  return (
    <div className={styles.wrapper}>
      <div className={`${styles.card} animate-fade-in`}>
        <div className={styles.logoBadge}>
          <span>Tecfluid VR Hub</span>
        </div>

        <h1 className={styles.title}>Iniciar Sesión</h1>
        <p className={styles.subtitle}>
          Ingresa y valida tu correo corporativo{" "}
          <span className={styles.domainHint}>@{requiredDomain}</span> para gestionar solicitudes de visores Meta Quest.
        </p>

        {/* Mensaje de éxito / instrucción */}
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
              textAlign: "left",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>✓</span>
            <span>{message}</span>
          </div>
        )}

        {/* Mensaje de error */}
        {error && (
          <div className={styles.errorText} style={{ marginBottom: "16px", textAlign: "left" }}>
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* PASO 1: Ingreso de correo corporativo */}
        {step === "request" && (
          <form onSubmit={handleRequestCode} className={styles.form}>
            <div>
              <label htmlFor="corp-email" className={styles.label}>
                Correo Corporativo
              </label>
              <div className={styles.inputGroup} style={{ marginTop: "6px" }}>
                <input
                  id="corp-email"
                  type="email"
                  placeholder={`nombre.apellido@${requiredDomain}`}
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (error) setError(null);
                  }}
                  className={styles.input}
                  required
                  autoComplete="email"
                  autoFocus
                />
              </div>
              <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "6px" }}>
                Enviaremos un código de seguridad de 6 dígitos a tu casilla de correo corporativo para validar tu identidad.
              </p>
            </div>

            <button
              type="submit"
              className={styles.submitBtn}
              disabled={!email.trim() || loading}
            >
              <span>{loading ? "Enviando código..." : "Enviar Código de Acceso"}</span>
              <span>✉️</span>
            </button>
          </form>
        )}

        {/* PASO 2: Verificación de código OTP */}
        {step === "verify" && (
          <form onSubmit={handleVerifyCode} className={styles.form}>
            <div>
              <label htmlFor="user-otp" className={styles.label}>
                Código de Verificación (6 dígitos)
              </label>
              <div className={styles.inputGroup} style={{ marginTop: "6px" }}>
                <input
                  id="user-otp"
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
                  onClick={handleReset}
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--accent-cyan)",
                    cursor: "pointer",
                    fontWeight: 600,
                  }}
                >
                  Cambiar correo / Reenviar
                </button>
              </div>
            </div>

            <button
              type="submit"
              className={styles.submitBtn}
              disabled={otpCode.length < 6 || loading}
            >
              <span>{loading ? "Validando..." : "Verificar e Ingresar"}</span>
              <span>→</span>
            </button>
          </form>
        )}

        <p className={styles.footerNote}>
          Sistema protegido y validado con Google Workspace y Google Calendar.
          <br /><br />
          <a
            href="/admin"
            style={{
              color: "var(--accent-blue)",
              textDecoration: "none",
              fontWeight: 500,
            }}
          >
            Acceso Administradores TI
          </a>
        </p>
      </div>
    </div>
  );
}
