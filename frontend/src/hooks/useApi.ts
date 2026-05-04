import axios from "axios";
import { useQuery } from "@tanstack/react-query";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1" });

// ── Types ──────────────────────────────────────────────────────────────────────
export interface Anomaly {
  id: string;
  timestamp: string;
  severity: "low" | "medium" | "high";
  anomaly_score: number;
  message: string;
  service: string;
  alerted: boolean;
}

export interface MetricsSummary {
  total_logs_ingested: number;
  anomalies_by_severity: Record<string, number>;
  top_services: { service: string; count: number }[];
  anomalies_over_time: { timestamp: string; count: number }[];
}

export interface AlertRule {
  id: number;
  name: string;
  webhook_url: string;
  min_severity: string;
  service_filter: string | null;
  active: boolean;
}

// ── Queries ────────────────────────────────────────────────────────────────────
export function useMetricsSummary() {
  return useQuery<MetricsSummary>({
    queryKey: ["metrics-summary"],
    queryFn: () => api.get("/metrics/summary").then((r) => r.data),
  });
}

export function useAnomalies(params: Record<string, string | number>) {
  return useQuery<{ total: number; results: Anomaly[] }>({
    queryKey: ["anomalies", params],
    queryFn: () => api.get("/anomalies", { params }).then((r) => r.data),
  });
}

export function useAlertRules() {
  return useQuery<AlertRule[]>({
    queryKey: ["alert-rules"],
    queryFn: () => api.get("/alerts/rules").then((r) => r.data),
  });
}

export const alertRulesApi = {
  create: (body: Omit<AlertRule, "id">) => api.post("/alerts/rules", body).then((r) => r.data),
  update: (id: number, body: Omit<AlertRule, "id">) => api.patch(`/alerts/rules/${id}`, body).then((r) => r.data),
  delete: (id: number) => api.delete(`/alerts/rules/${id}`),
};
