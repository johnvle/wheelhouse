import type { Position } from "./position";

export interface DashboardSummary {
  total_premium_collected: number;
  premium_mtd: number;
  open_position_count: number;
  upcoming_expirations: Position[];
}

export interface TickerSummary {
  ticker: string;
  total_premium: number;
  trade_count: number;
  avg_annualized_roc: number;
}
