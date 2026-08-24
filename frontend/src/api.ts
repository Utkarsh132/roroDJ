import type { AudioAnalysis, ChatResponse, CreativeRole } from "./types";

const DEPLOY_API_URL = "__PORT_8000__";
const API_URL =
  import.meta.env.VITE_API_URL ||
  (DEPLOY_API_URL.startsWith("__") ? "http://localhost:8000" : DEPLOY_API_URL);

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }
  return response.json() as Promise<T>;
}

export async function sendChat(
  sessionId: string,
  role: CreativeRole,
  message: string,
): Promise<ChatResponse> {
  const response = await fetch(`${API_URL}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, role, message }),
  });
  return parseResponse<ChatResponse>(response);
}

export async function analyzeAudio(file: File): Promise<AudioAnalysis> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`${API_URL}/api/v1/audio/analyze`, {
    method: "POST",
    body,
  });
  return parseResponse<AudioAnalysis>(response);
}
