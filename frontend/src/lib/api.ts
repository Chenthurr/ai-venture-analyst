import { useAuthStore } from "@/lib/store";

const BASE = ""; // rewrites proxy /api/* to the backend, see next.config.js

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: Omit<RequestInit, "body"> & { body?: any; form?: FormData } = {}
): Promise<T> {
  const token = useAuthStore.getState().token;
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let body = options.body;
  if (options.form) {
    body = options.form; // browser sets multipart boundary automatically
  } else if (body && typeof body !== "string") {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(body);
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers, body });

  if (res.status === 401) {
    useAuthStore.getState().logout();
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      /* no JSON body */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // --- auth ---
  register: (payload: { email: string; password: string; full_name?: string }) =>
    request("/api/auth/register", { method: "POST", body: payload as any }),

  login: async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const res = await fetch(`${BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new ApiError(res.status, data.detail || "Login failed");
    }
    return res.json() as Promise<{ access_token: string; token_type: string }>;
  },

  me: () => request("/api/auth/me"),

  // --- projects ---
  listProjects: () => request<any[]>("/api/projects"),
  createProject: (payload: any) =>
    request("/api/projects", { method: "POST", body: payload }),
  getProject: (id: string) => request<any>(`/api/projects/${id}`),
  updateProject: (id: string, payload: any) =>
    request(`/api/projects/${id}`, { method: "PATCH", body: payload }),
  deleteProject: (id: string) =>
    request(`/api/projects/${id}`, { method: "DELETE" }),

  // --- documents ---
  listDocuments: (projectId: string) =>
    request<any[]>(`/api/projects/${projectId}/documents`),
  uploadDocument: (projectId: string, file: File, docCategory?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (docCategory) form.append("doc_category", docCategory);
    return request(`/api/projects/${projectId}/documents`, {
      method: "POST",
      form,
    });
  },
  deleteDocument: (projectId: string, documentId: string) =>
    request(`/api/projects/${projectId}/documents/${documentId}`, {
      method: "DELETE",
    }),

  // --- financials ---
  submitFinancials: (projectId: string, payload: any) =>
    request(`/api/projects/${projectId}/financials`, {
      method: "POST",
      body: payload,
    }),
  getLatestFinancials: (projectId: string) =>
    request<any>(`/api/projects/${projectId}/financials/latest`),
  getFinancialMetrics: (projectId: string) =>
    request<any>(`/api/projects/${projectId}/financials/metrics`),
  getValuation: (projectId: string) =>
    request<any>(`/api/projects/${projectId}/financials/valuation`),

  // --- analysis ---
  runAnalysis: (projectId: string) =>
    request<any>(`/api/projects/${projectId}/analysis`, { method: "POST" }),
  getLatestAnalysis: (projectId: string) =>
    request<any>(`/api/projects/${projectId}/analysis/latest`),
  chat: (projectId: string, question: string) =>
    request<any>(`/api/projects/${projectId}/analysis/chat`, {
      method: "POST",
      body: { question },
    }),

  // --- dashboard ---
  getDashboardSummary: () => request<any>("/api/dashboard/summary"),

  // --- reports ---
  downloadReport: async (
    projectId: string,
    reportType: "investment-memo" | "board-report" | "investor-report" | "due-diligence-checklist",
    suggestedFilename: string
  ) => {
    const token = useAuthStore.getState().token;
    const res = await fetch(`${BASE}/api/projects/${projectId}/reports/${reportType}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new ApiError(res.status, data.detail || "Failed to generate report");
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = suggestedFilename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};

export { ApiError };
