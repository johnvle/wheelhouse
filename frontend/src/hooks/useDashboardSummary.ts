import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import { getDashboardSummary, type DashboardFilters } from "@/lib/api";
import type { DashboardSummary } from "@/types/dashboard";

export function useDashboardSummary(params: DashboardFilters = {}) {
  const { session } = useAuth();
  const token = session?.access_token ?? null;

  return useQuery<DashboardSummary>({
    queryKey: ["dashboard", "summary", params.start, params.end],
    queryFn: () => getDashboardSummary(params, token),
    enabled: !!token,
  });
}
