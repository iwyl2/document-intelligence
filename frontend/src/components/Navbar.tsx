"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Cpu, FileText, Lock, LogOut } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { checkBackendHealth } from "@/lib/api";
import { LoginModal } from "./LoginModal";

export function Navbar() {
  const pathname = usePathname();
  const { isAuthenticated, logout } = useAuth();
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    checkBackendHealth().then(setBackendOnline);
    const interval = setInterval(() => {
      checkBackendHealth().then(setBackendOnline);
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          {/* Logo & Brand */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg group-hover:border-emerald-500/40 transition-colors">
              <Cpu className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold tracking-tight text-zinc-100 flex items-center gap-1.5">
                DocIntel <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">v1</span>
              </span>
              <span className="text-[10px] text-zinc-400 font-mono -mt-0.5">
                Grounded RAG Engine
              </span>
            </div>
          </Link>

          {/* Navigation Links & Actions */}
          <nav className="flex items-center gap-4">
            {/* Backend Health Badge */}
            <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-1 rounded-full border border-zinc-800 bg-zinc-900/60">
              <span
                className={`w-2 h-2 rounded-full ${
                  backendOnline === true
                    ? "bg-emerald-500 animate-pulse"
                    : backendOnline === false
                    ? "bg-rose-500"
                    : "bg-zinc-600"
                }`}
              />
              <span className="text-zinc-400">
                API: {backendOnline === true ? "Online" : backendOnline === false ? "Offline" : "Checking"}
              </span>
            </div>

            <Link
              href="/"
              className={`text-xs font-medium transition-colors ${
                pathname === "/" ? "text-zinc-100" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Overview
            </Link>

            {isAuthenticated ? (
              <>
                <Link
                  href="/workspace"
                  className={`text-xs font-medium transition-colors ${
                    pathname === "/workspace" ? "text-emerald-400 font-semibold" : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  Workspace
                </Link>
                <button
                  onClick={logout}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900 border border-transparent hover:border-zinc-800 rounded-lg transition-colors"
                  title="Lock workspace session"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Exit</span>
                </button>
              </>
            ) : (
              <button
                onClick={() => setIsLoginModalOpen(true)}
                className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-semibold rounded-lg shadow-sm transition-all"
              >
                <Lock className="w-3.5 h-3.5" />
                Launch Workspace
              </button>
            )}
          </nav>
        </div>
      </header>

      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        redirectTo="/workspace"
      />
    </>
  );
}
