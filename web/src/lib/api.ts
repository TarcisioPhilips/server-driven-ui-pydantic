import type { ClientVersion, ScreenResponse } from "../types/sdui";
import { V1_COMPONENTS, V2_COMPONENTS } from "../types/sdui";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

function headersFor(version: ClientVersion): HeadersInit {
  const supported = version === 1 ? V1_COMPONENTS : V2_COMPONENTS;
  return {
    "X-Client-Version": String(version),
    "X-Supported-Components": supported.join(","),
    "Content-Type": "application/json",
  };
}

export async function fetchScreen(
  screenId: string,
  version: ClientVersion,
  simulateUnknown = false,
): Promise<ScreenResponse> {
  const qs = simulateUnknown ? "?simulate_unknown=true" : "";
  const res = await fetch(`${API_BASE}/screens/${screenId}${qs}`, {
    headers: headersFor(version),
  });
  if (!res.ok) {
    throw new Error(`Failed to load screen ${screenId}: ${res.status}`);
  }
  return res.json() as Promise<ScreenResponse>;
}

export async function agentScreen(
  prompt: string,
  version: ClientVersion,
  simulateUnknown = false,
): Promise<ScreenResponse> {
  const res = await fetch(`${API_BASE}/agent/screen`, {
    method: "POST",
    headers: headersFor(version),
    body: JSON.stringify({ prompt, simulate_unknown: simulateUnknown }),
  });
  if (!res.ok) {
    throw new Error(`Agent failed: ${res.status}`);
  }
  return res.json() as Promise<ScreenResponse>;
}

export async function submitAction(
  endpoint: string,
  version: ClientVersion,
): Promise<{ ok: boolean; next_screen?: ScreenResponse }> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: headersFor(version),
  });
  if (!res.ok) {
    throw new Error(`Submit failed: ${res.status}`);
  }
  return res.json() as Promise<{ ok: boolean; next_screen?: ScreenResponse }>;
}
