import type { QueryResponse, SessionPayload } from "../types";

const API = import.meta.env.VITE_API_URL || "";

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail.map((d: { msg?: string }) => d.msg).join(" ");
    return body.error || "Request failed.";
  } catch {
    return "Request failed.";
  }
}

export async function uploadFiles(files: File[], sessionId?: string | null): Promise<SessionPayload> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  if (sessionId) form.append("session_id", sessionId);
  const res = await fetch(`${API}/api/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function loadDemo(sessionId?: string | null): Promise<SessionPayload> {
  const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
  const res = await fetch(`${API}/api/demo${qs}`, { method: "POST" });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function getSession(sessionId: string): Promise<SessionPayload> {
  const res = await fetch(`${API}/api/session/${sessionId}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function deleteFile(sessionId: string, fileId: string): Promise<SessionPayload> {
  const res = await fetch(`${API}/api/session/${sessionId}/files/${fileId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function resetSession(sessionId: string): Promise<SessionPayload> {
  const res = await fetch(`${API}/api/session/${sessionId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function askQuestion(sessionId: string, question: string): Promise<QueryResponse> {
  const res = await fetch(`${API}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
