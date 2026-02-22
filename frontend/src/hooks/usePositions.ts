import { useQuery } from "@tanstack/react-query";
import type { Position } from "@/types/position";
import { useAuth } from "@/hooks/useAuth";
import { getPositions, type PositionFilters } from "@/lib/api";

export function usePositions(params: PositionFilters = {}) {
  const { session } = useAuth();
  const token = session?.access_token ?? null;

  return useQuery<Position[]>({
    queryKey: ["positions", params],
    queryFn: () => getPositions(params, token),
    enabled: !!token,
  });
}
