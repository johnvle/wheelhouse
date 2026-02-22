import { useQuery } from "@tanstack/react-query";
import type { Position, PositionStatus } from "@/types/position";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface UsePositionsParams {
  status?: PositionStatus;
  ticker?: string;
  sort?: string;
  order?: "asc" | "desc";
}

async function fetchPositions(
  params: UsePositionsParams,
  token: string | null
): Promise<Position[]> {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set("status", params.status);
  if (params.ticker) searchParams.set("ticker", params.ticker);
  if (params.sort) searchParams.set("sort", params.sort);
  if (params.order) searchParams.set("order", params.order);

  const url = `${API_BASE}/api/v1/positions?${searchParams.toString()}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch positions: ${res.status}`);
  }
  return res.json();
}

export function usePositions(
  params: UsePositionsParams = {},
  token: string | null = null
) {
  return useQuery<Position[]>({
    queryKey: ["positions", params],
    queryFn: () => fetchPositions(params, token),
  });
}
