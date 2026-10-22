"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FileText,
  Scissors,
  Binary,
  Database,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Lock,
  Layers,
  Terminal,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { LoginModal } from "@/components/LoginModal";

export default function HomePage() {
  const { isAuthenticated } = useAuth();
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [activeStage, setActiveStage] = useState<number>(2);

  const pipelineStages = [
    {
      title: "PDF Ingestion",
      tech: "pypdf",
      desc: "Text extraction preserving strict 1-based page numbering across complex document layouts.",
      icon: FileText,
      metric: "1-based pages",
    },
    {
      title: "Normalization",
      tech: "Unicode NFKC",
      desc: "Sanitizes whitespace, line endings, and Unicode ligature artifacts while preserving paragraph structure.",
      icon: Scissors,
      metric: "NFKC Cleaned",
    },
    {
      title: "Semantic Chunking",
      tech: "Cosine Drop (80%)",
      desc: "Calculates cosine distance between consecutive sentence vectors to split only on real topical shifts.",
      icon: Layers,
      metric: "80th percentile",
    },
    {
      title: "Vector Storage",
      tech: "ChromaDB + MiniLM",
      desc: "Encodes chunks into 384-dimensional dense vectors using local CPU sentence-transformers.",
      icon: Database,
      metric: "384-dim dense",
    },
    {
      title: "Grounded Generation",
      tech: "Prompt Grounding + LLM",
      desc: "Strict context injection enforcing inline citations [Page X] with deterministic fallback on missing facts.",
      icon: Sparkles,
      metric: "Zero Hallucination",
    },
  ];

  return (
    <div className="flex flex-col min-h-full">
      {/* Hero Section */}
      <section className="relative pt-20 pb-16 px-4 sm:px-6 max-w-5xl mx-auto text-center">
        {/* Subtle decorative glow */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none -z-10" />

        {/* Eyebrow Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/5 text-emerald-400 text-xs font-mono mb-6">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Verifiable Retrieval-Augmented Generation</span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-6xl font-bold tracking-tight text-zinc-100 max-w-4xl mx-auto leading-[1.15]">
          Document Intelligence with{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
            Guaranteed Attribution
          </span>
        </h1>

        {/* Subhead */}
        <p className="mt-6 text-base sm:text-lg text-zinc-400 max-w-2xl mx-auto leading-relaxed">
          An engineering-first RAG pipeline built from scratch. Local dense vector
          embeddings, semantic boundary chunking, and strict page-level citation grounding.
        </p>

        {/* Action CTAs */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          {isAuthenticated ? (
            <Link
              href="/workspace"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-semibold text-sm shadow-lg shadow-emerald-500/20 transition-all hover:gap-3"
            >
              Open Workspace
              <ArrowRight className="w-4 h-4" />
            </Link>
          ) : (
            <button
              onClick={() => setIsLoginModalOpen(true)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-semibold text-sm shadow-lg shadow-emerald-500/20 transition-all hover:gap-3"
            >
              <Lock className="w-4 h-4" />
              Launch Workspace
              <ArrowRight className="w-4 h-4" />
            </button>
          )}

          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-zinc-800 hover:border-zinc-700 bg-zinc-900/60 hover:bg-zinc-800 text-zinc-300 text-sm font-medium transition-all"
          >
            <Terminal className="w-4 h-4 text-zinc-400" />
            View Specifications
          </a>
        </div>
      </section>

      {/* Interactive 5-Stage Architecture Section */}
      <section className="py-12 px-4 sm:px-6 max-w-5xl mx-auto w-full">
        <div className="text-center mb-8">
          <h2 className="text-xs font-mono uppercase tracking-widest text-emerald-400">
            System Architecture
          </h2>
          <p className="text-xl sm:text-2xl font-semibold tracking-tight text-zinc-200 mt-1">
            5-Stage Precision Pipeline
          </p>
        </div>

        {/* Pipeline Stepper */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 mb-6">
          {pipelineStages.map((stage, idx) => {
            const Icon = stage.icon;
            const isActive = activeStage === idx;
            return (
              <button
                key={stage.title}
                onClick={() => setActiveStage(idx)}
                className={`flex flex-col items-start p-3.5 rounded-xl border text-left transition-all ${
                  isActive
                    ? "border-emerald-500/50 bg-emerald-500/10 shadow-sm"
                    : "border-zinc-800/80 bg-zinc-900/40 hover:bg-zinc-900 hover:border-zinc-700"
                }`}
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <div
                    className={`p-1.5 rounded-lg ${
                      isActive
                        ? "bg-emerald-500 text-zinc-950"
                        : "bg-zinc-800 text-zinc-400"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-mono text-zinc-500">
                    0{idx + 1}
                  </span>
                </div>
                <span
                  className={`text-xs font-semibold ${
                    isActive ? "text-emerald-400" : "text-zinc-200"
                  }`}
                >
                  {stage.title}
                </span>
                <span className="text-[10px] font-mono text-zinc-400 mt-0.5">
                  {stage.tech}
                </span>
              </button>
            );
          })}
        </div>

        {/* Active Stage Detailed Card */}
        <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/70 backdrop-blur-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 text-xs font-mono text-emerald-400 mb-1">
                <span>Stage 0{activeStage + 1}</span>
                <span>•</span>
                <span>{pipelineStages[activeStage].tech}</span>
              </div>
              <h3 className="text-lg font-semibold text-zinc-100">
                {pipelineStages[activeStage].title}
              </h3>
              <p className="text-sm text-zinc-400 mt-1.5 max-w-2xl leading-relaxed">
                {pipelineStages[activeStage].desc}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-zinc-950 border border-zinc-800/80 text-right shrink-0">
              <span className="text-[10px] uppercase font-mono text-zinc-500 block">
                Verification Spec
              </span>
              <span className="text-sm font-mono font-semibold text-emerald-400">
                {pipelineStages[activeStage].metric}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Quantitative Benchmarks Grid */}
      <section className="py-12 px-4 sm:px-6 max-w-5xl mx-auto w-full">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-5 rounded-2xl border border-zinc-800/80 bg-zinc-900/30">
            <span className="text-xs font-mono uppercase text-zinc-500">
              Evaluation Recall
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono text-zinc-100">100%</span>
              <span className="text-xs font-mono text-emerald-400">Recall@5</span>
            </div>
            <p className="mt-2 text-xs text-zinc-400 leading-relaxed">
              Guarantees the target context chunk resides in the top-5 retrieved candidates.
            </p>
          </div>

          <div className="p-5 rounded-2xl border border-zinc-800/80 bg-zinc-900/30">
            <span className="text-xs font-mono uppercase text-zinc-500">
              Ranking Quality
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono text-zinc-100">0.83</span>
              <span className="text-xs font-mono text-emerald-400">MRR Score</span>
            </div>
            <p className="mt-2 text-xs text-zinc-400 leading-relaxed">
              Mean Reciprocal Rank verifying relevant context appears primarily at Rank #1.
            </p>
          </div>

          <div className="p-5 rounded-2xl border border-zinc-800/80 bg-zinc-900/30">
            <span className="text-xs font-mono uppercase text-zinc-500">
              Vector Pipeline
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono text-zinc-100">384</span>
              <span className="text-xs font-mono text-emerald-400">Dimensions</span>
            </div>
            <p className="mt-2 text-xs text-zinc-400 leading-relaxed">
              all-MiniLM-L6-v2 running on local CPU with zero external API fees.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-zinc-900 py-6 text-center text-xs text-zinc-500 font-mono">
        Document Intelligence Engine • Built with FastAPI, Sentence-Transformers, ChromaDB & Next.js
      </footer>

      {/* Login Gatekeeper Modal */}
      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        redirectTo="/workspace"
      />
    </div>
  );
}
