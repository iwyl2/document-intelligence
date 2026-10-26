"use client";

import React, { createContext, useContext, useSyncExternalStore } from "react";

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (passcode: string) => boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isLoading: false,
  login: () => false,
  logout: () => {},
});

const EXPECTED_PASSCODE =
  process.env.NEXT_PUBLIC_WORKSPACE_PASSCODE || "doc-intel-2026";

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

function getSnapshot(): boolean {
  try {
    return sessionStorage.getItem("doc_intel_session") === "authenticated";
  } catch {
    return false;
  }
}

function getServerSnapshot(): boolean {
  return false;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const login = (passcode: string): boolean => {
    if (passcode.trim() === EXPECTED_PASSCODE.trim()) {
      try {
        sessionStorage.setItem("doc_intel_session", "authenticated");
        window.dispatchEvent(new Event("storage"));
      } catch {
        // Ignore
      }
      return true;
    }
    return false;
  };

  const logout = () => {
    try {
      sessionStorage.removeItem("doc_intel_session");
      window.dispatchEvent(new Event("storage"));
    } catch {
      // Ignore
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading: false, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
