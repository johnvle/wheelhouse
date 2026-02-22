import { useQuery } from "@tanstack/react-query";
import type { Position, PositionStatus } from "@/types/position";
import { useAuth } from "@/hooks/useAuth";
import { apiFetch } from "@/lib/api";

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

  return apiFetch(`/api/v1/positions?${searchParams.toString()}`, token);
}

export function usePositions(params: UsePositionsParams = {}) {
  const { session } = useAuth();
  const token = session?.access_token ?? null;

  return useQuery<Position[]>({
    queryKey: ["positions", params],
    queryFn: () => fetchPositions(params, token),
    enabled: !!token,
  });
}
