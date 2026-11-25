import crypto from "node:crypto";

const SECRET = process.env.SECRET_KEY || "tecfluid-metaquest-secret-key-2024-secure";

export interface TokenPayload {
  sub: string;
  role: "user" | "admin";
  email: string;
  iat?: number;
  exp?: number;
  [key: string]: unknown;
}

// Generador de Token JWT (HMAC-SHA256, sin dependencias externas)
export function createAccessToken(payload: TokenPayload, expiresInHours = 8): string {
  const header = { alg: "HS256", typ: "JWT" };
  const now = Math.floor(Date.now() / 1000);
  const fullPayload = {
    ...payload,
    iat: now,
    exp: now + expiresInHours * 3600,
  };

  const b64Header = Buffer.from(JSON.stringify(header)).toString("base64url");
  const b64Payload = Buffer.from(JSON.stringify(fullPayload)).toString("base64url");
  const signature = crypto
    .createHmac("sha256", SECRET)
    .update(`${b64Header}.${b64Payload}`)
    .digest("base64url");

  return `${b64Header}.${b64Payload}.${signature}`;
}

export function verifyAccessToken(token: string): TokenPayload {
  const parts = token.split(".");
  if (parts.length !== 3) {
    throw new Error("Token malformado o inválido.");
  }

  const [b64Header, b64Payload, signature] = parts;
  const expectedSignature = crypto
    .createHmac("sha256", SECRET)
    .update(`${b64Header}.${b64Payload}`)
    .digest("base64url");

  if (signature !== expectedSignature) {
    throw new Error("Firma de seguridad no válida.");
  }

  const payload: TokenPayload = JSON.parse(Buffer.from(b64Payload, "base64url").toString());
  const now = Math.floor(Date.now() / 1000);
  if (payload.exp && payload.exp < now) {
    throw new Error("La sesión ha expirado.");
  }

  return payload;
}

// Almacén en memoria para códigos OTP (10 minutos)
interface OTPRecord {
  code: string;
  expiresAt: number;
}

const userOtpStore = new Map<string, OTPRecord>();
const adminOtpStore = new Map<string, OTPRecord>();

export function saveUserOtp(email: string, code: string): void {
  userOtpStore.set(email.toLowerCase().trim(), {
    code,
    expiresAt: Date.now() + 10 * 60 * 1000,
  });
}

export function verifyUserOtp(email: string, code: string): boolean {
  const cleanEmail = email.toLowerCase().trim();
  const record = userOtpStore.get(cleanEmail);
  if (!record) return false;
  if (Date.now() > record.expiresAt) {
    userOtpStore.delete(cleanEmail);
    return false;
  }
  if (record.code === code.trim()) {
    userOtpStore.delete(cleanEmail);
    return true;
  }
  return false;
}

export function saveAdminOtp(email: string, code: string): void {
  adminOtpStore.set(email.toLowerCase().trim(), {
    code,
    expiresAt: Date.now() + 10 * 60 * 1000,
  });
}

export function verifyAdminOtp(email: string, code: string): boolean {
  const cleanEmail = email.toLowerCase().trim();
  const record = adminOtpStore.get(cleanEmail);
  if (!record) return false;
  if (Date.now() > record.expiresAt) {
    adminOtpStore.delete(cleanEmail);
    return false;
  }
  if (record.code === code.trim()) {
    adminOtpStore.delete(cleanEmail);
    return true;
  }
  return false;
}
