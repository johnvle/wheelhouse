import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import { getPrices } from "@/lib/api";
import type { PriceResponse } from "@/types/price";

export function usePrices(tickers: string[]) {
  const { session } = useAuth();
  const token = session?.access_token ?? null;

  // Deduplicate and sort for stable query key
  const uniqueTickers = [...new Set(tickers)].sort();
  const tickerKey = uniqueTickers.join(",");

  return useQuery<PriceResponse>({
    queryKey: ["prices", tickerKey],
    queryFn: () => getPrices(uniqueTickers, token),
    enabled: !!token && uniqueTickers.length > 0,
    refetchInterval: 60_000, // 60 seconds
  });
}
