"use client";

import React, { useState, useRef } from "react";
import {
  UploadCloud,
  FileText,
  Send,
  Loader2,
  Lock,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  SlidersHorizontal,
  Bookmark,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { LoginModal } from "@/components/LoginModal";
import { uploadDocument, queryDocument, UploadResponse } from "@/lib/api";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citedPages?: number[];
  isGrounded?: boolean;
  timestamp: string;
}

export default function WorkspacePage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  // Ingestion state
  const [uploadedDoc, setUploadedDoc] = useState<UploadResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Query & Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [topK, setTopK] = useState(3);
  const [isQuerying, setIsQuerying] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);

  // Sample prompt suggestions
  const suggestedQueries = [
    "What practical experience do students get in the program?",
    "What are the module assessments and coursework requirements?",
    "What technical events or competitions can students join?",
  ];

  // File Upload Handlers
  const handleFileSelect = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Only PDF files are supported.");
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      const res = await uploadDocument(file);
      setUploadedDoc(res);
      // Add a system welcome message
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content: `Document "${res.file_name}" successfully indexed into in-memory ChromaDB (${res.num_pages} pages, ${res.num_chunks} semantic chunks). You can now ask questions with verifiable page citations!`,
          isGrounded: true,
          citedPages: [],
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to upload document";
      setUploadError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  // Query Handler
  const handleSendQuery = async (queryText?: string) => {
    const question = (queryText || inputQuery).trim();
    if (!question || isQuerying) return;

    if (!uploadedDoc) {
      setQueryError("Please upload a PDF document before asking questions.");
      return;
    }

    setQueryError(null);
    setInputQuery("");

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsQuerying(true);

    try {
      const response = await queryDocument(question, topK);

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.answer,
        citedPages: response.cited_pages,
        isGrounded: response.is_grounded,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to query document";
      setQueryError(msg);
    } finally {
      setIsQuerying(false);
    }
  };

  // Helper to highlight [Page X] citations in assistant responses
  const renderFormattedAnswer = (text: string) => {
    const parts = text.split(/(\[Page\s+\d+\])/g);
    return parts.map((part, index) => {
      const match = part.match(/\[Page\s+(\d+)\]/);
      if (match) {
        return (
          <span
            key={index}
            className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 rounded-md bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-mono text-xs font-semibold select-all"
            title={`Verified from Page ${match[1]}`}
          >
            <Bookmark className="w-3 h-3" />
            Page {match[1]}
          </span>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  if (authLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
      </div>
    );
  }

  // Gatekeeper: Not authenticated
  if (!isAuthenticated) {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="max-w-md w-full p-8 rounded-2xl border border-zinc-800 bg-zinc-900/60 backdrop-blur-md text-center">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-4">
            <Lock className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold tracking-tight text-zinc-100">
            Workspace Locked
          </h2>
          <p className="mt-2 text-sm text-zinc-400 leading-relaxed">
            The V1 backend uses an in-memory ChromaDB vector store. Please authenticate
            to initiate your working session.
          </p>
          <button
            onClick={() => setIsLoginModalOpen(true)}
            className="mt-6 w-full py-2.5 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-semibold text-sm shadow-md transition-all"
          >
            Unlock Workspace Session
          </button>
          <LoginModal
            isOpen={isLoginModalOpen}
            onClose={() => setIsLoginModalOpen(false)}
            redirectTo="/workspace"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[calc(100vh-4rem)]">
      {/* LEFT COLUMN: Document Management (4 cols) */}
      <div className="lg:col-span-4 flex flex-col gap-4">
        {/* Upload Card */}
        <div className="p-5 rounded-2xl border border-zinc-800 bg-zinc-900/50 backdrop-blur-sm flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-400" />
              Document Ingestion
            </h2>
            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-zinc-800 text-zinc-400">
              In-Memory
            </span>
          </div>

          {/* Drag & Drop Area */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-zinc-800 hover:border-emerald-500/50 hover:bg-zinc-900/60 transition-all rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer group"
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileSelect(e.target.files[0]);
                }
              }}
              accept=".pdf"
              className="hidden"
            />
            {isUploading ? (
              <div className="flex flex-col items-center gap-2">
                <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
                <span className="text-xs font-mono text-zinc-300">
                  Chunking & Indexing...
                </span>
              </div>
            ) : (
              <>
                <div className="p-3 rounded-full bg-zinc-800 group-hover:bg-emerald-500/10 group-hover:text-emerald-400 text-zinc-400 transition-colors mb-2">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <span className="text-xs font-medium text-zinc-200">
                  Drop PDF here or click to browse
                </span>
                <span className="text-[11px] text-zinc-500 font-mono mt-1">
                  Text-based PDFs only (v1)
                </span>
              </>
            )}
          </div>

          {uploadError && (
            <div className="mt-3 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-400 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{uploadError}</span>
            </div>
          )}

          {/* Uploaded Document Summary */}
          {uploadedDoc && (
            <div className="mt-4 p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5">
              <div className="flex items-start justify-between">
                <div className="min-w-0 pr-2">
                  <span className="text-[10px] uppercase font-mono text-emerald-400 font-semibold block">
                    Active Document
                  </span>
                  <p className="text-xs font-medium text-zinc-200 truncate mt-0.5" title={uploadedDoc.file_name}>
                    {uploadedDoc.file_name}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setUploadedDoc(null);
                    setMessages([]);
                  }}
                  className="p-1 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded transition-colors"
                  title="Clear document"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-emerald-500/10 text-xs font-mono">
                <div>
                  <span className="text-zinc-500 block text-[10px]">Pages</span>
                  <span className="text-zinc-200 font-semibold">{uploadedDoc.num_pages}</span>
                </div>
                <div>
                  <span className="text-zinc-500 block text-[10px]">Semantic Chunks</span>
                  <span className="text-emerald-400 font-semibold">{uploadedDoc.num_chunks}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Parameters Card */}
        <div className="p-5 rounded-2xl border border-zinc-800 bg-zinc-900/50 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
              <SlidersHorizontal className="w-3.5 h-3.5 text-zinc-400" />
              Retrieval Parameters
            </h3>
            <span className="text-xs font-mono text-emerald-400 font-semibold">
              Top-K: {topK}
            </span>
          </div>
          <input
            type="range"
            min={1}
            max={5}
            step={1}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="w-full accent-emerald-500 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] font-mono text-zinc-500 mt-1">
            <span>1 chunk</span>
            <span>3 (recommended)</span>
            <span>5 chunks</span>
          </div>
        </div>
      </div>

      {/* RIGHT COLUMN: Grounded Chat & Citations (8 cols) */}
      <div className="lg:col-span-8 flex flex-col rounded-2xl border border-zinc-800 bg-zinc-900/30 backdrop-blur-sm overflow-hidden h-[calc(100vh-6rem)]">
        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 text-zinc-400">
              <div className="p-3 bg-zinc-800/60 rounded-2xl text-emerald-400 mb-3 border border-zinc-700/60">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-base font-semibold text-zinc-200">
                {uploadedDoc ? "Document Ready for Queries" : "Upload a PDF to Begin"}
              </h3>
              <p className="text-xs text-zinc-400 max-w-sm mt-1 leading-relaxed">
                {uploadedDoc
                  ? "Ask any question about the document. The engine will retrieve context and cite exact page numbers."
                  : "Drag and drop a PDF on the left panel to trigger text extraction, semantic chunking, and ChromaDB vector indexing."}
              </p>

              {/* Suggestions */}
              {uploadedDoc && (
                <div className="mt-6 flex flex-col gap-2 w-full max-w-md">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 text-left">
                    Suggested Questions
                  </span>
                  {suggestedQueries.map((q) => (
                    <button
                      key={q}
                      onClick={() => handleSendQuery(q)}
                      className="text-left text-xs p-2.5 rounded-xl border border-zinc-800 bg-zinc-900/70 hover:bg-zinc-800/80 hover:border-zinc-700 text-zinc-300 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${
                  msg.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl p-4 text-xs sm:text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-emerald-500 text-zinc-950 font-medium rounded-br-xs"
                      : "bg-zinc-900 border border-zinc-800/80 text-zinc-200 rounded-bl-xs"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <div>{renderFormattedAnswer(msg.content)}</div>
                  ) : (
                    <div>{msg.content}</div>
                  )}

                  {/* Grounding & Attribution Footer */}
                  {msg.role === "assistant" && msg.isGrounded !== undefined && (
                    <div className="mt-3 pt-2.5 border-t border-zinc-800 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono">
                      <div className="flex items-center gap-1.5">
                        {msg.isGrounded ? (
                          <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Grounded Answer
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-amber-400 font-semibold">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            Fallback: Not Found in Context
                          </span>
                        )}
                      </div>

                      {msg.citedPages && msg.citedPages.length > 0 && (
                        <span className="text-zinc-400">
                          Cited Pages:{" "}
                          <span className="text-emerald-400 font-bold">
                            [{msg.citedPages.join(", ")}]
                          </span>
                        </span>
                      )}
                    </div>
                  )}
                </div>
                <span className="text-[10px] font-mono text-zinc-500 px-1 mt-1">
                  {msg.timestamp}
                </span>
              </div>
            ))
          )}

          {isQuerying && (
            <div className="flex items-start">
              <div className="max-w-[85%] rounded-2xl p-4 bg-zinc-900 border border-zinc-800 text-zinc-400 flex items-center gap-2 text-xs">
                <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />
                <span>Retrieving context & generating verified answer...</span>
              </div>
            </div>
          )}
        </div>

        {/* Query Input Bar */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-950/80">
          {queryError && (
            <div className="mb-2 text-xs text-rose-400 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              <span>{queryError}</span>
            </div>
          )}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendQuery();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder={
                uploadedDoc
                  ? "Ask a question about the document..."
                  : "Upload a document to enable queries..."
              }
              disabled={!uploadedDoc || isQuerying}
              className="flex-1 py-2.5 px-4 bg-zinc-900 border border-zinc-800 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-xl text-xs sm:text-sm text-zinc-100 placeholder-zinc-500 outline-none disabled:opacity-50 transition-all"
            />
            <button
              type="submit"
              disabled={!uploadedDoc || !inputQuery.trim() || isQuerying}
              className="p-2.5 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 text-zinc-950 font-semibold rounded-xl shadow-sm transition-all"
              aria-label="Send question"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
