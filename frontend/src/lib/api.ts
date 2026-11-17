export interface UserResponse {
  id: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface DocumentRecordResponse {
  id: string;
  file_name: string;
  num_pages: number;
  num_chunks: number;
  uploaded_at: string;
}

export interface WorkspaceResponse {
  id: string;
  name: string;
  created_at: string;
  documents: DocumentRecordResponse[];
}

export interface CitationSource {
  file_name: string;
  page_number: number;
}

export interface QueryResponse {
  answer: string;
  cited_sources: CitationSource[];
  cited_pages: number[];
  is_grounded: boolean;
}

export interface UploadResponse {
  file_name: string;
  num_pages: number;
  num_chunks: number;
  message: string;
}

export interface IndexStatusResponse {
  total_chunks: number;
  indexed_files: string[];
  is_empty: boolean;
}

export interface ApiError {
  detail: string;
  error_type?: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeaders(token?: string | null, sessionId?: string | null): Record<string, string> {
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (sessionId) {
    headers["X-Session-ID"] = sessionId;
  }
  return headers;
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { method: "GET" });
    return res.ok;
  } catch {
    return false;
  }
}

// ---------------- AUTHENTICATION ---------------- //

export async function loginApi(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(errorData.detail || `Login failed with status ${res.status}`);
  }

  return res.json();
}

export async function registerApi(email: string, password: string): Promise<UserResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Registration failed" }));
    throw new Error(errorData.detail || `Registration failed with status ${res.status}`);
  }

  return res.json();
}

export async function getMeApi(token: string): Promise<UserResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
    method: "GET",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to fetch user profile" }));
    throw new Error(errorData.detail || `User fetch failed with status ${res.status}`);
  }

  return res.json();
}

export async function listUsersApi(token: string): Promise<UserResponse[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/users`, {
    method: "GET",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to list users" }));
    throw new Error(errorData.detail || `List users failed with status ${res.status}`);
  }

  return res.json();
}

export async function updateUserStatusApi(
  token: string,
  userId: string,
  isActive: boolean
): Promise<UserResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/users/${userId}/status`, {
    method: "PATCH",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ is_active: isActive }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to update user status" }));
    throw new Error(errorData.detail || `Update user failed with status ${res.status}`);
  }

  return res.json();
}

// ---------------- WORKSPACES ---------------- //

export async function getWorkspacesApi(token: string): Promise<WorkspaceResponse[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/workspaces/`, {
    method: "GET",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to fetch workspaces" }));
    throw new Error(errorData.detail || `Workspaces fetch failed with status ${res.status}`);
  }

  return res.json();
}

export async function createWorkspaceApi(token: string, name: string): Promise<WorkspaceResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/workspaces/`, {
    method: "POST",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to create workspace" }));
    throw new Error(errorData.detail || `Workspace creation failed with status ${res.status}`);
  }

  return res.json();
}

export async function getWorkspaceApi(token: string, workspaceId: string): Promise<WorkspaceResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/workspaces/${workspaceId}`, {
    method: "GET",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to fetch workspace" }));
    throw new Error(errorData.detail || `Workspace fetch failed with status ${res.status}`);
  }

  return res.json();
}

export async function deleteWorkspaceApi(token: string, workspaceId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/workspaces/${workspaceId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to delete workspace" }));
    throw new Error(errorData.detail || `Workspace deletion failed with status ${res.status}`);
  }
}

// ---------------- DOCUMENTS & QUERY ---------------- //

export async function getIndexStatus(
  token?: string | null,
  sessionId?: string | null
): Promise<IndexStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/documents/status`, {
    method: "GET",
    headers: authHeaders(token, sessionId),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to get index status" }));
    throw new Error(errorData.detail || `Status check failed with code ${res.status}`);
  }

  return res.json();
}

export async function clearDocuments(
  token?: string | null,
  sessionId?: string | null
): Promise<{ message: string; total_chunks: number }> {
  const res = await fetch(`${API_BASE_URL}/api/v1/documents`, {
    method: "DELETE",
    headers: authHeaders(token, sessionId),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to clear documents" }));
    throw new Error(errorData.detail || `Clear failed with code ${res.status}`);
  }

  return res.json();
}

export async function uploadDocument(
  file: File,
  token?: string | null,
  sessionId?: string | null
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
    method: "POST",
    headers: authHeaders(token, sessionId),
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(errorData.detail || `Upload failed with status ${res.status}`);
  }

  return res.json();
}

export async function queryDocument(
  question: string,
  top_k: number = 3,
  token?: string | null,
  sessionId?: string | null
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/query`, {
    method: "POST",
    headers: {
      ...authHeaders(token, sessionId),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question, top_k }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Query failed" }));
    throw new Error(errorData.detail || `Query failed with status ${res.status}`);
  }

  return res.json();
}
