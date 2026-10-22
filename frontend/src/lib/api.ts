export interface UploadResponse {
  file_name: string;
  num_pages: number;
  num_chunks: number;
  message: string;
}

export interface QueryResponse {
  answer: string;
  cited_pages: number[];
  is_grounded: boolean;
}

export interface ApiError {
  detail: string;
  error_type?: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { method: "GET" });
    return res.ok;
  } catch {
    return false;
  }
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
    method: "POST",
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
  top_k: number = 3
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/query`, {
    method: "POST",
    headers: {
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
