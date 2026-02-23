import { supabase } from "@/lib/supabase";
import type { Account, AccountCreate, AccountUpdate } from "@/types/account";
import type { DashboardSummary, TickerSummary } from "@/types/dashboard";
import type { Position, PositionType, PositionStatus } from "@/types/position";
import type { PriceResponse } from "@/types/price";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// Mutex for token refresh — prevents concurrent refresh calls
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = supabase.auth
    .refreshSession()
    .then(({ data, error }) => {
      if (error || !data.session) {
        window.location.href = "/login";
        return null;
      }
      return data.session.access_token;
    })
    .finally(() => {
      refreshPromise = null;
    });
  return refreshPromise;
}

async function parseErrorBody(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((d: { msg: string }) => d.msg).join("; ");
    }
  } catch {
    // JSON parsing failed — fall through
  }
  return `API error: ${res.status}`;
}

export async function apiFetch<T>(
  path: string,
  token: string | null,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) ?? {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401 && token) {
    const newToken = await refreshAccessToken();
    if (!newToken) throw new Error("Session expired");
    headers["Authorization"] = `Bearer ${newToken}`;
    const retry = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (!retry.ok) {
      throw new Error(await parseErrorBody(retry));
    }
    return retry.json();
  }

  if (!res.ok) {
    throw new Error(await parseErrorBody(res));
  }

  return res.json();
}

// --- Accounts ---

export function getAccounts(token: string | null): Promise<Account[]> {
  return apiFetch("/api/v1/accounts", token);
}

export function createAccount(
  body: AccountCreate,
  token: string | null
): Promise<Account> {
  return apiFetch("/api/v1/accounts", token, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updateAccount(
  id: string,
  body: AccountUpdate,
  token: string | null
): Promise<Account> {
  return apiFetch(`/api/v1/accounts/${id}`, token, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

// --- Positions ---

export interface PositionFilters {
  status?: PositionStatus;
  ticker?: string;
  type?: PositionType;
  account_id?: string;
  expiration_start?: string;
  expiration_end?: string;
  sort?: string;
  order?: "asc" | "desc";
}

export function getPositions(
  params: PositionFilters,
  token: string | null
): Promise<Position[]> {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value != null) searchParams.set(key, value);
  }
  return apiFetch(`/api/v1/positions?${searchParams.toString()}`, token);
}

export interface PositionCreateBody {
  account_id: string;
  ticker: string;
  type: PositionType;
  open_date: string;
  expiration_date: string;
  strike_price: number;
  contracts: number;
  premium_per_share: number;
  multiplier?: number;
  open_fees?: number;
  notes?: string | null;
  tags?: string[] | null;
}

export function createPosition(
  body: PositionCreateBody,
  token: string | null
): Promise<Position> {
  return apiFetch("/api/v1/positions", token, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updatePosition(
  id: string,
  body: Partial<PositionCreateBody>,
  token: string | null
): Promise<Position> {
  return apiFetch(`/api/v1/positions/${id}`, token, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export interface PositionCloseBody {
  outcome: "EXPIRED" | "ASSIGNED" | "CLOSED_EARLY";
  close_date: string;
  close_price_per_share?: number | null;
  close_fees?: number | null;
}

export function closePosition(
  id: string,
  body: PositionCloseBody,
  token: string | null
): Promise<Position> {
  return apiFetch(`/api/v1/positions/${id}/close`, token, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export interface PositionRollBody {
  close: {
    close_date: string;
    close_price_per_share?: number | null;
    close_fees?: number | null;
  };
  open: PositionCreateBody;
}

export interface PositionRollResponse {
  closed: Position;
  opened: Position;
}

export function rollPosition(
  id: string,
  body: PositionRollBody,
  token: string | null
): Promise<PositionRollResponse> {
  return apiFetch(`/api/v1/positions/${id}/roll`, token, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// --- Dashboard ---

export interface DashboardFilters {
  start?: string;
  end?: string;
}

export function getDashboardSummary(
  params: DashboardFilters,
  token: string | null
): Promise<DashboardSummary> {
  const searchParams = new URLSearchParams();
  if (params.start) searchParams.set("start", params.start);
  if (params.end) searchParams.set("end", params.end);
  return apiFetch(
    `/api/v1/dashboard/summary?${searchParams.toString()}`,
    token
  );
}

// --- Prices ---

export function getPrices(
  tickers: string[],
  token: string | null
): Promise<PriceResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set("tickers", tickers.join(","));
  return apiFetch(`/api/v1/prices?${searchParams.toString()}`, token);
}

export function getDashboardByTicker(
  params: DashboardFilters,
  token: string | null
): Promise<TickerSummary[]> {
  const searchParams = new URLSearchParams();
  if (params.start) searchParams.set("start", params.start);
  if (params.end) searchParams.set("end", params.end);
  return apiFetch(
    `/api/v1/dashboard/by-ticker?${searchParams.toString()}`,
    token
  );
}

// --- Export ---

export interface ExportFilters {
  status?: PositionStatus;
  ticker?: string;
  start?: string;
  end?: string;
}

export async function exportPositionsCsv(
  params: ExportFilters,
  token: string | null
): Promise<void> {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value != null) searchParams.set(key, value);
  }

  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(
    `${API_BASE}/api/v1/export/positions.csv?${searchParams.toString()}`,
    { headers }
  );

  if (res.status === 401 && token) {
    const newToken = await refreshAccessToken();
    if (!newToken) throw new Error("Session expired");
    headers["Authorization"] = `Bearer ${newToken}`;
    const retry = await fetch(
      `${API_BASE}/api/v1/export/positions.csv?${searchParams.toString()}`,
      { headers }
    );
    if (!retry.ok) throw new Error(`Export failed: ${retry.status}`);
    await triggerDownload(retry);
    return;
  }

  if (!res.ok) {
    throw new Error(`Export failed: ${res.status}`);
  }

  await triggerDownload(res);
}

async function triggerDownload(res: Response): Promise<void> {
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition");
  const match = disposition?.match(/filename="?([^"]+)"?/);
  const filename = match?.[1] ?? `positions_${new Date().toISOString().slice(0, 10)}.csv`;

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
