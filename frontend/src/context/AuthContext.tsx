"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (passcode: string) => boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isLoading: true,
  login: () => false,
  logout: () => {},
});

const EXPECTED_PASSCODE =
  process.env.NEXT_PUBLIC_WORKSPACE_PASSCODE || "doc-intel-2026";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    try {
      const stored = sessionStorage.getItem("doc_intel_session");
      if (stored === "authenticated") {
        setIsAuthenticated(true);
      }
    } catch {
      // Ignore sessionStorage errors (e.g. incognito/disabled)
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = (passcode: string): boolean => {
    if (passcode.trim() === EXPECTED_PASSCODE.trim()) {
      setIsAuthenticated(true);
      try {
        sessionStorage.setItem("doc_intel_session", "authenticated");
      } catch {
        // Ignore
      }
      return true;
    }
    return false;
  };

  const logout = () => {
    setIsAuthenticated(false);
    try {
      sessionStorage.removeItem("doc_intel_session");
    } catch {
      // Ignore
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
