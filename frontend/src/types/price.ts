export interface TickerPrice {
  ticker: string;
  current_price: number | null;
  change_percent: number | null;
  last_fetched: string | null;
}

export interface PriceResponse {
  prices: TickerPrice[];
}
