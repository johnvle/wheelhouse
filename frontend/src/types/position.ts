export type PositionType = "COVERED_CALL" | "CASH_SECURED_PUT";
export type PositionStatus = "OPEN" | "CLOSED";
export type PositionOutcome =
  | "EXPIRED"
  | "ASSIGNED"
  | "CLOSED_EARLY"
  | "ROLLED";

export interface Position {
  id: string;
  user_id: string;
  account_id: string;
  ticker: string;
  type: PositionType;
  status: PositionStatus;
  open_date: string;
  expiration_date: string;
  close_date: string | null;
  strike_price: number;
  contracts: number;
  multiplier: number;
  premium_per_share: number;
  open_fees: number;
  close_fees: number;
  close_price_per_share: number | null;
  outcome: PositionOutcome | null;
  roll_group_id: string | null;
  notes: string | null;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
  // Computed fields
  premium_total: number;
  premium_net: number;
  collateral: number;
  roc_period: number;
  dte: number;
  annualized_roc: number;
}
