"use client";

import { useState, useSyncExternalStore } from "react";
import CorporateLogin from "../components/CorporateLogin";
import ReservationForm from "../components/ReservationForm";
import VRBackgroundCanvas from "../components/VRBackgroundCanvas";

const emptySubscribe = () => () => {};

export default function Home() {
  const isClient = useSyncExternalStore(emptySubscribe, () => true, () => false);
  const [userEmail, setUserEmail] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      const savedUser = window.sessionStorage.getItem("tecfluid_vr_user");
      if (savedUser && savedUser.endsWith("@grupotecfluid.com")) {
        return savedUser;
      }
    }
    return null;
  });
  const [authToken, setAuthToken] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      return window.sessionStorage.getItem("tecfluid_vr_token");
    }
    return null;
  });

  const handleLogin = (email: string, token: string) => {
    setUserEmail(email);
    setAuthToken(token);
    if (typeof window !== "undefined") {
      window.sessionStorage.setItem("tecfluid_vr_user", email);
      window.sessionStorage.setItem("tecfluid_vr_token", token);
    }
  };

  const handleLogout = () => {
    setUserEmail(null);
    setAuthToken(null);
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem("tecfluid_vr_user");
      window.sessionStorage.removeItem("tecfluid_vr_token");
    }
  };

  if (!isClient) {
    return null; // Evitar disparidad de hidratación SSR/Cliente
  }

  return (
    <>
      <VRBackgroundCanvas />
      <main>
        {!userEmail ? (
          <CorporateLogin
            onLogin={handleLogin}
            requiredDomain="grupotecfluid.com"
          />
        ) : (
          <ReservationForm
            userEmail={userEmail}
            authToken={authToken || undefined}
            onLogout={handleLogout}
          />
        )}
      </main>
    </>
  );
}

