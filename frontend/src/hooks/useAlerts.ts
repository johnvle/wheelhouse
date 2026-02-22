import { useMemo, useState, useEffect, useRef } from "react";
import type { Position } from "@/types/position";
import type { TickerPrice } from "@/types/price";

export interface Alert {
  id: string;
  type: "expiration" | "near_strike" | "stale_price";
  message: string;
  positionId?: string;
  ticker?: string;
}

// Default thresholds (will be overridden by settings in US-034)
const EXPIRATION_WARNING_DAYS = 7;
const NEAR_STRIKE_THRESHOLD = 0.05;
const STALE_PRICE_MINUTES = 5;

function computeAlerts(
  positions: Position[],
  priceMap: Record<string, TickerPrice>
): Alert[] {
  const alerts: Alert[] = [];
  const now = Date.now();
  const staleCutoff = STALE_PRICE_MINUTES * 60 * 1000;

  // Track which tickers we've already flagged as stale
  const staleTickers = new Set<string>();

  for (const pos of positions) {
    // Expiration alert
    const expDate = new Date(pos.expiration_date).getTime();
    const daysUntilExp = (expDate - now) / (1000 * 60 * 60 * 24);
    if (daysUntilExp <= EXPIRATION_WARNING_DAYS && daysUntilExp >= 0) {
      const daysText =
        daysUntilExp < 1
          ? "today"
          : `in ${Math.ceil(daysUntilExp)} day${Math.ceil(daysUntilExp) === 1 ? "" : "s"}`;
      alerts.push({
        id: `exp-${pos.id}`,
        type: "expiration",
        message: `${pos.ticker} ${pos.type === "COVERED_CALL" ? "CC" : "CSP"} $${pos.strike_price} expires ${daysText}`,
        positionId: pos.id,
        ticker: pos.ticker,
      });
    }

    // Price near strike alert
    const tickerPrice = priceMap[pos.ticker];
    if (tickerPrice?.current_price != null) {
      const price = tickerPrice.current_price;
      const strike = pos.strike_price;
      let nearStrike = false;

      if (pos.type === "COVERED_CALL") {
        nearStrike = price >= strike * (1 - NEAR_STRIKE_THRESHOLD);
      } else {
        nearStrike = price <= strike * (1 + NEAR_STRIKE_THRESHOLD);
      }

      if (nearStrike) {
        alerts.push({
          id: `near-${pos.id}`,
          type: "near_strike",
          message: `${pos.ticker} price ($${price.toFixed(2)}) is near ${pos.type === "COVERED_CALL" ? "CC" : "CSP"} strike ($${strike})`,
          positionId: pos.id,
          ticker: pos.ticker,
        });
      }

      // Stale price alert (one per ticker)
      if (!staleTickers.has(pos.ticker) && tickerPrice.last_fetched) {
        const fetched = new Date(tickerPrice.last_fetched).getTime();
        if (now - fetched > staleCutoff) {
          staleTickers.add(pos.ticker);
          alerts.push({
            id: `stale-${pos.ticker}`,
            type: "stale_price",
            message: `${pos.ticker} price data is stale (last updated >5 min ago)`,
            ticker: pos.ticker,
          });
        }
      }
    }
  }

  return alerts;
}

export function useAlerts(
  positions: Position[] | undefined,
  priceMap: Record<string, TickerPrice>
) {
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());

  // Track the price data timestamp to reset dismissals on refresh
  const priceTimestampRef = useRef<string | null>(null);

  // Compute a fingerprint from price data to detect refreshes
  const priceFingerprint = useMemo(() => {
    const entries = Object.values(priceMap);
    if (entries.length === 0) return null;
    return entries.map((p) => p.last_fetched ?? "").join("|");
  }, [priceMap]);

  // Reset dismissed alerts when price data refreshes
  useEffect(() => {
    if (priceFingerprint && priceFingerprint !== priceTimestampRef.current) {
      if (priceTimestampRef.current !== null) {
        // Price data actually changed — reset dismissals
        setDismissedIds(new Set());
      }
      priceTimestampRef.current = priceFingerprint;
    }
  }, [priceFingerprint]);

  const allAlerts = useMemo(
    () => computeAlerts(positions ?? [], priceMap),
    [positions, priceMap]
  );

  const activeAlerts = useMemo(
    () => allAlerts.filter((a) => !dismissedIds.has(a.id)),
    [allAlerts, dismissedIds]
  );

  function dismiss(alertId: string) {
    setDismissedIds((prev) => new Set([...prev, alertId]));
  }

  function dismissAll() {
    setDismissedIds(new Set(allAlerts.map((a) => a.id)));
  }

  return { alerts: activeAlerts, dismiss, dismissAll };
}
