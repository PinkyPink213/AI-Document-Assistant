export interface HealthResponse {
  status: "ok" | "error";
  service?: string;
  timestamp?: string;
}

export interface DatabaseHealthResponse {
  status: "ok" | "error";
  database: "connected" | "disconnected";
  detail?: string;
}
