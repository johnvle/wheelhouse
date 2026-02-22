import { supabase } from "@/lib/supabase";
import type { Account, AccountCreate, AccountUpdate } from "@/types/account";
import type { DashboardSummary, TickerSummary } from "@/types/dashboard";
import type { Position, PositionType, PositionStatus } from "@/types/position";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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
    // Try refreshing the session
    const { data, error } = await supabase.auth.refreshSession();
    if (error || !data.session) {
      // Refresh failed — redirect to login
      window.location.href = "/login";
      throw new Error("Session expired");
    }
    // Retry with new token
    headers["Authorization"] = `Bearer ${data.session.access_token}`;
    const retry = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (!retry.ok) {
      throw new Error(`API error: ${retry.status}`);
    }
    return retry.json();
  }

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
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
