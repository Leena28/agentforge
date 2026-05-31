import axios from "axios";
import type {
  Agent,
  WorkflowTemplate,
  WorkflowRun,
  Metrics,
} from "../types";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE,
  headers: { "Content-Type": "application/json" },
});

// AGENTS
export const getAgents = () =>
  api.get<Agent[]>("/api/agents").then((r) => r.data);

export const getAgent = (id: string) =>
  api.get<Agent>(`/api/agents/${id}`).then((r) => r.data);

export const createAgent = (payload: Partial<Agent>) =>
  api.post<Agent>("/api/agents", payload).then((r) => r.data);

export const updateAgent = (id: string, payload: Partial<Agent>) =>
  api.patch<Agent>(`/api/agents/${id}`, payload).then((r) => r.data);

export const deleteAgent = (id: string) =>
  api.delete(`/api/agents/${id}`);

// TEMPLATES
export const getTemplates = () =>
  api.get<WorkflowTemplate[]>("/api/templates").then((r) => r.data);

export const getTemplate = (key: string) =>
  api.get<WorkflowTemplate>(`/api/templates/${key}`).then((r) => r.data);

export const createTemplate = (payload: Partial<WorkflowTemplate>) =>
  api.post<WorkflowTemplate>("/api/templates", payload).then((r) => r.data);

// RUNS
export const getRuns = (limit = 20) =>
  api.get<WorkflowRun[]>(`/api/runs?limit=${limit}`).then((r) => r.data);

export const getRun = (id: string) =>
  api.get<WorkflowRun>(`/api/runs/${id}`).then((r) => r.data);

export const startRun = (payload: {
  template_key: string;
  input_message: string;
  channel?: string;
}) => api.post<{ run_id: string; status: string }>("/api/runs", payload).then((r) => r.data);

export const approveRun = (id: string, payload: { approved_by: string; notes?: string }) =>
  api.post<WorkflowRun>(`/api/runs/${id}/approve`, payload).then((r) => r.data);

// MONITORING
export const getMetrics = () =>
  api.get<Metrics>("/api/monitoring/metrics").then((r) => r.data);

// SSE STREAM
export const createEventStream = (runId: string) =>
  new EventSource(`${BASE}/api/runs/${runId}/events/stream`);