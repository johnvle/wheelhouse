import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import { getDashboardByTicker, type DashboardFilters } from "@/lib/api";
import type { TickerSummary } from "@/types/dashboard";

export function useDashboardByTicker(params: DashboardFilters = {}) {
  const { session } = useAuth();
  const token = session?.access_token ?? null;

  return useQuery<TickerSummary[]>({
    queryKey: ["dashboard", "by-ticker", params.start, params.end],
    queryFn: () => getDashboardByTicker(params, token),
    enabled: !!token,
  });
}
