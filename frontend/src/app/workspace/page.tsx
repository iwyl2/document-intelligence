"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  UploadCloud,
  FileText,
  Send,
  Loader2,
  Lock,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  SlidersHorizontal,
  Bookmark,
  Trash2,
  FolderPlus,
  Layers,
  Calendar,
  X,
  FileCheck,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { LoginModal } from "@/components/LoginModal";
import {
  uploadDocument,
  queryDocument,
  getIndexStatus,
  clearDocuments,
  getWorkspacesApi,
  createWorkspaceApi,
  deleteWorkspaceApi,
  deleteDocumentApi,
  WorkspaceResponse,
  IndexStatusResponse,
  CitationSource,
} from "@/lib/api";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citedSources?: CitationSource[];
  citedPages?: number[];
  isGrounded?: boolean;
  timestamp: string;
}

export default function WorkspacePage() {
  const { user, token, isAuthenticated, isLoading: authLoading } = useAuth();
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  // Workspaces State
  const [workspaces, setWorkspaces] = useState<WorkspaceResponse[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState("");
  const [isWorkspacesLoading, setIsWorkspacesLoading] = useState(false);

  // Ingestion & Status
  const [indexStatus, setIndexStatus] = useState<IndexStatusResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Query & Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [topK, setTopK] = useState(3);
  const [isQuerying, setIsQuerying] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);

  const activeWorkspace = workspaces.find((w) => w.id === activeWorkspaceId) || null;

  // Fetch workspaces for current user
  const loadWorkspaces = useCallback(async () => {
    if (!token) return;
    setIsWorkspacesLoading(true);
    try {
      const data = await getWorkspacesApi(token);
      setWorkspaces(data);
      if (data.length > 0 && !activeWorkspaceId) {
        setActiveWorkspaceId(data[0].id);
      }
    } catch {
      // Ignored if offline
    } finally {
      setIsWorkspacesLoading(false);
    }
  }, [token, activeWorkspaceId]);

  // Fetch status of active workspace vector store
  const refreshStatus = useCallback(async () => {
    if (!token || !activeWorkspaceId) return;
    try {
      const status = await getIndexStatus(token, activeWorkspaceId);
      setIndexStatus(status);
    } catch {
      // Backend might be offline
    }
  }, [token, activeWorkspaceId]);

  // Load workspaces on authentication
  useEffect(() => {
    if (isAuthenticated && token) {
      loadWorkspaces();
    }
  }, [isAuthenticated, token, loadWorkspaces]);

  // Refresh status when active workspace changes
  useEffect(() => {
    if (activeWorkspaceId && token) {
      refreshStatus();
      setMessages([]);
      setUploadError(null);
      setQueryError(null);
    }
  }, [activeWorkspaceId, token, refreshStatus]);

  // Handle Workspace Creation
  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !newWorkspaceName.trim()) return;

    try {
      const created = await createWorkspaceApi(token, newWorkspaceName.trim());
      setWorkspaces((prev) => [created, ...prev]);
      setActiveWorkspaceId(created.id);
      setNewWorkspaceName("");
      setIsCreatingWorkspace(false);
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Failed to create workspace");
    }
  };

  // Handle Workspace Deletion
  const handleDeleteWorkspace = async (workspaceId: string) => {
    if (!token) return;
    if (!confirm("Are you sure you want to delete this workspace and its vector index?")) return;

    try {
      await deleteWorkspaceApi(token, workspaceId);
      setWorkspaces((prev) => prev.filter((w) => w.id !== workspaceId));
      if (activeWorkspaceId === workspaceId) {
        const remaining = workspaces.filter((w) => w.id !== workspaceId);
        setActiveWorkspaceId(remaining.length > 0 ? remaining[0].id : null);
      }
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Failed to delete workspace");
    }
  };

  // File Upload Handlers
  const handleFileSelect = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Only PDF documents are supported (.pdf).");
      return;
    }

    if (!token || !activeWorkspaceId) {
      setUploadError("Please select or create an active workspace first.");
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      const res = await uploadDocument(file, token, activeWorkspaceId);
      await loadWorkspaces();
      await refreshStatus();

      // Add system announcement message
      setMessages((prev) => [
        ...prev,
        {
          id: `sys-${crypto.randomUUID()}`,
          role: "assistant",
          content: `Document "${res.file_name}" successfully indexed into workspace "${activeWorkspace?.name || "Active Workspace"}" (${res.num_pages} pages, ${res.num_chunks} semantic chunks). Ask any question with cross-document verifiable citations!`,
          isGrounded: true,
          citedSources: [],
          citedPages: [],
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Failed to upload and index PDF.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // Clear workspace index
  const handleClearIndex = async () => {
    if (!token || !activeWorkspaceId) return;
    if (!confirm("Clear all indexed document chunks in this workspace?")) return;

    setIsClearing(true);
    try {
      await clearDocuments(token, activeWorkspaceId);
      await loadWorkspaces();
      await refreshStatus();
      setMessages([]);
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Failed to clear documents.");
    } finally {
      setIsClearing(false);
    }
  };

  // Delete a specific document
  const handleDeleteDocument = async (documentId: string, fileName: string) => {
    if (!token || !activeWorkspaceId) return;
    if (!confirm(`Delete document "${fileName}" and all its vector chunks?`)) return;

    try {
      await deleteDocumentApi(documentId, token, activeWorkspaceId);
      await loadWorkspaces();
      await refreshStatus();
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Failed to delete document.");
    }
  };

  // Query Submit Handler
  const handleQuerySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isQuerying) return;

    if (!token || !activeWorkspaceId) {
      setQueryError("Please select an active workspace first.");
      return;
    }

    const currentQuery = inputQuery.trim();
    setInputQuery("");
    setQueryError(null);

    const userMessage: ChatMessage = {
      id: `usr-${crypto.randomUUID()}`,
      role: "user",
      content: currentQuery,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsQuerying(true);

    try {
      const response = await queryDocument(currentQuery, topK, token, activeWorkspaceId);
      const assistantMessage: ChatMessage = {
        id: `ast-${crypto.randomUUID()}`,
        role: "assistant",
        content: response.answer,
        citedSources: response.cited_sources,
        citedPages: response.cited_pages,
        isGrounded: response.is_grounded,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: unknown) {
      setQueryError(err instanceof Error ? err.message : "Failed to query document.");
    } finally {
      setIsQuerying(false);
    }
  };

  // Helper to format inline citations nicely
  const renderMessageContent = (text: string) => {
    // Regex for [file_name • Page X] or [Page X]
    const regex = /\[([^•\]]+?\s*•\s*[Pp]age\s*\d+|[Pp]age\s*\d+)\]/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }
      parts.push(
        <span
          key={`cite-${match.index}`}
          className="inline-flex items-center gap-1 px-1.5 py-0.5 mx-1 my-0.5 rounded text-[11px] font-mono font-medium bg-emerald-500/15 border border-emerald-500/30 text-emerald-300"
        >
          <Bookmark className="w-3 h-3 text-emerald-400" />
          {match[1]}
        </span>
      );
      lastIndex = regex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  // Sample prompt suggestions
  const suggestedQueries = [
    "What practical experience do students get in the program?",
    "What are the module assessments and coursework requirements?",
    "What technical events or competitions can students join?",
  ];

  if (authLoading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      {/* Auth Banner if not signed in */}
      {!isAuthenticated && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Lock className="w-5 h-5 text-amber-400 shrink-0" />
            <div>
              <p className="text-sm font-semibold">Authentication Required</p>
              <p className="text-xs text-amber-400/80">
                Sign in or register to access isolated multi-tenant workspaces and document indexing.
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsLoginModalOpen(true)}
            className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-amber-400 hover:bg-amber-300 text-zinc-950 transition-all shrink-0"
          >
            Sign In / Register
          </button>
        </div>
      )}

      {/* Top Workspace Selector Header */}
      <div className="p-4 rounded-2xl bg-zinc-950 border border-zinc-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-zinc-100 flex items-center gap-2">
              Workspace Environment
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-400">
                Multi-Tenant v2
              </span>
            </h1>
            <p className="text-xs text-zinc-400">
              Select or create isolated workspaces for cross-referencing multiple PDFs
            </p>
          </div>
        </div>

        {isAuthenticated && (
          <div className="flex items-center gap-2.5 flex-wrap">
            {/* Workspace Select Dropdown */}
            <select
              value={activeWorkspaceId || ""}
              onChange={(e) => setActiveWorkspaceId(e.target.value)}
              className="px-3 py-1.5 text-xs font-medium bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 outline-none focus:border-emerald-500"
            >
              {workspaces.map((ws) => (
                <option key={ws.id} value={ws.id}>
                  {ws.name} ({ws.documents.length} docs)
                </option>
              ))}
            </select>

            <button
              onClick={() => setIsCreatingWorkspace(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-200 rounded-lg transition-colors"
            >
              <FolderPlus className="w-3.5 h-3.5 text-emerald-400" />
              New Workspace
            </button>

            {activeWorkspace && (
              <button
                onClick={() => handleDeleteWorkspace(activeWorkspace.id)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-950/30 border border-rose-900/40 rounded-lg transition-colors"
                title="Delete this workspace and vector index"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Create Workspace Inline Modal */}
      {isCreatingWorkspace && (
        <div className="p-4 bg-zinc-900/90 border border-emerald-500/30 rounded-2xl flex items-center justify-between gap-4 animate-in fade-in">
          <form onSubmit={handleCreateWorkspace} className="flex items-center gap-3 flex-1">
            <FolderPlus className="w-5 h-5 text-emerald-400 shrink-0" />
            <input
              type="text"
              required
              value={newWorkspaceName}
              onChange={(e) => setNewWorkspaceName(e.target.value)}
              placeholder="Enter workspace name (e.g. Legal Research, Semester 1)..."
              autoFocus
              className="flex-1 px-3 py-2 text-xs bg-zinc-950 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              className="px-3.5 py-2 text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-zinc-950 rounded-lg transition-colors"
            >
              Create Workspace
            </button>
            <button
              type="button"
              onClick={() => setIsCreatingWorkspace(false)}
              className="p-2 text-zinc-400 hover:text-zinc-200 rounded-lg"
            >
              <X className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}

      {/* Main Workspace Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Documents & Ingestion (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Upload Card */}
          <div className="p-5 rounded-2xl bg-zinc-950 border border-zinc-800 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                <UploadCloud className="w-4 h-4 text-emerald-400" />
                Upload PDF Document
              </h2>
              {activeWorkspace && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
                  {activeWorkspace.documents.length} File(s)
                </span>
              )}
            </div>

            {/* Dropzone */}
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-zinc-800 hover:border-emerald-500/50 rounded-xl p-6 text-center cursor-pointer transition-colors bg-zinc-900/40 hover:bg-zinc-900/80 group"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileSelect(file);
                }}
              />
              <div className="mx-auto w-10 h-10 rounded-full bg-zinc-800 group-hover:bg-emerald-500/20 text-zinc-400 group-hover:text-emerald-400 flex items-center justify-center mb-3 transition-colors">
                {isUploading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <UploadCloud className="w-5 h-5" />
                )}
              </div>
              <p className="text-xs font-semibold text-zinc-200">
                {isUploading ? "Extracting & Chunking..." : "Click or drag PDF to index"}
              </p>
              <p className="text-[11px] text-zinc-500 mt-1">
                Vectorized via all-MiniLM-L6-v2 in ChromaDB
              </p>
            </div>

            {uploadError && (
              <div className="flex items-start gap-2 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs rounded-xl">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{uploadError}</span>
              </div>
            )}
          </div>

          {/* Workspace Document Records */}
          <div className="p-5 rounded-2xl bg-zinc-950 border border-zinc-800 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
              <FileCheck className="w-3.5 h-3.5 text-emerald-400" />
              Indexed Documents ({activeWorkspace?.documents.length || 0})
            </h3>

            {activeWorkspace && activeWorkspace.documents.length > 0 ? (
              <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {activeWorkspace.documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="p-3 bg-zinc-900/70 border border-zinc-800/80 rounded-xl space-y-1 hover:border-zinc-700 transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 truncate flex-1 min-w-0">
                        <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span className="text-xs font-semibold text-zinc-200 truncate">
                          {doc.file_name}
                        </span>
                      </div>
                      <button
                        onClick={() => handleDeleteDocument(doc.id, doc.file_name)}
                        title="Delete document and vector chunks"
                        className="p-1 text-zinc-500 hover:text-rose-400 rounded transition-colors shrink-0"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-zinc-400 font-mono">
                      <span>{doc.num_pages} Pages • {doc.num_chunks} Chunks</span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3 text-zinc-500" />
                        {new Date(doc.uploaded_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-zinc-500 italic py-2">
                No documents uploaded yet in this workspace.
              </p>
            )}

            {/* In-Memory Vector Store Details */}
            {indexStatus && !indexStatus.is_empty && (
              <div className="pt-3 border-t border-zinc-900 flex items-center justify-between text-xs text-zinc-400">
                <span className="font-mono text-[11px]">
                  Total Chunks: <strong className="text-emerald-400">{indexStatus.total_chunks}</strong>
                </span>
                <button
                  onClick={handleClearIndex}
                  disabled={isClearing}
                  className="text-xs text-rose-400 hover:text-rose-300 font-medium"
                >
                  {isClearing ? "Clearing..." : "Clear Chunks"}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Grounded Q&A Chat (8 cols) */}
        <div className="lg:col-span-8 flex flex-col h-[750px] bg-zinc-950 border border-zinc-800 rounded-2xl overflow-hidden shadow-xl">
          {/* Chat Header */}
          <div className="px-5 py-4 border-b border-zinc-800/80 flex items-center justify-between bg-zinc-900/40">
            <div className="flex items-center gap-2.5">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <div>
                <h2 className="text-sm font-semibold text-zinc-100">
                  Grounded Q&A Engine
                </h2>
                <p className="text-[11px] text-zinc-400">
                  Answers generated strictly from indexed chunks with inline <code className="text-emerald-400 font-mono">[file • Page X]</code> citations
                </p>
              </div>
            </div>

            {/* Top-K Slider Control */}
            <div className="flex items-center gap-2 bg-zinc-900 px-3 py-1.5 rounded-xl border border-zinc-800 text-xs text-zinc-300">
              <SlidersHorizontal className="w-3.5 h-3.5 text-zinc-400" />
              <span className="font-mono text-[11px]">Top-K Context:</span>
              <input
                type="range"
                min="1"
                max="8"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-16 accent-emerald-500 cursor-pointer"
              />
              <span className="font-mono font-bold text-emerald-400 w-3">{topK}</span>
            </div>
          </div>

          {/* Chat Message Stream */}
          <div className="flex-1 p-5 overflow-y-auto space-y-4">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400">
                  <Sparkles className="w-6 h-6 text-emerald-400" />
                </div>
                <div className="max-w-md">
                  <h3 className="text-sm font-semibold text-zinc-200">
                    Ready to Answer Across Documents
                  </h3>
                  <p className="text-xs text-zinc-400 mt-1">
                    Upload documents to this workspace, then ask questions. Every factual claim will cite the exact document and page.
                  </p>
                </div>

                {/* Prompt Suggestions */}
                <div className="grid grid-cols-1 gap-2 w-full max-w-lg pt-2">
                  {suggestedQueries.map((query, i) => (
                    <button
                      key={i}
                      onClick={() => setInputQuery(query)}
                      className="text-left text-xs p-2.5 rounded-xl bg-zinc-900/80 hover:bg-zinc-900 border border-zinc-800/80 hover:border-zinc-700 text-zinc-300 transition-colors"
                    >
                      &quot;{query}&quot;
                    </button>
                  ))}
                </div>
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
                    className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed space-y-2 ${
                      msg.role === "user"
                        ? "bg-emerald-600 text-white font-medium"
                        : "bg-zinc-900 border border-zinc-800/90 text-zinc-200"
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{renderMessageContent(msg.content)}</div>

                    {/* Citations Footer for Assistant */}
                    {msg.role === "assistant" && (
                      <div className="pt-2 border-t border-zinc-800/80 flex flex-wrap items-center justify-between gap-2 text-[10px]">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          {msg.citedSources && msg.citedSources.length > 0 ? (
                            msg.citedSources.map((source, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono flex items-center gap-1"
                              >
                                <Bookmark className="w-3 h-3 text-emerald-400" />
                                {source.file_name} • Page {source.page_number}
                              </span>
                            ))
                          ) : msg.isGrounded ? (
                            <span className="text-emerald-400 flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" />
                              Grounded in Context
                            </span>
                          ) : (
                            <span className="text-amber-400 flex items-center gap-1">
                              <AlertTriangle className="w-3 h-3" />
                              Fallback Response (Unverified)
                            </span>
                          )}
                        </div>
                        <span className="text-zinc-500 font-mono">{msg.timestamp}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}

            {isQuerying && (
              <div className="flex items-center gap-2 p-3 bg-zinc-900 border border-zinc-800 rounded-2xl max-w-xs text-xs text-zinc-400">
                <Loader2 className="w-4 h-4 animate-spin text-emerald-400 shrink-0" />
                <span>Searching ChromaDB & generating grounded answer...</span>
              </div>
            )}
          </div>

          {/* Chat Input Bar */}
          <div className="p-4 border-t border-zinc-800 bg-zinc-900/60">
            {queryError && (
              <p className="text-xs text-rose-400 mb-2">{queryError}</p>
            )}
            <form onSubmit={handleQuerySubmit} className="flex items-center gap-2">
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder={
                  !isAuthenticated
                    ? "Sign in to query workspace..."
                    : activeWorkspace?.documents.length === 0
                    ? "Upload a PDF above before asking questions..."
                    : "Ask a question across indexed documents..."
                }
                disabled={!isAuthenticated || isQuerying}
                className="flex-1 px-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-xs text-zinc-100 placeholder-zinc-500 outline-none focus:border-emerald-500 disabled:opacity-50 transition-all"
              />
              <button
                type="submit"
                disabled={!inputQuery.trim() || isQuerying || !isAuthenticated}
                className="p-2.5 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 text-zinc-950 rounded-xl transition-all shrink-0 font-semibold"
                aria-label="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      </div>

      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        redirectTo="/workspace"
      />
    </div>
  );
}
