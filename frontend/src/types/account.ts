export type Broker = "robinhood" | "merrill" | "other";

export interface Account {
  id: string;
  user_id: string;
  name: string;
  broker: Broker;
  tax_treatment: string | null;
  created_at: string;
  updated_at: string;
}

export interface AccountCreate {
  name: string;
  broker: Broker;
  tax_treatment?: string | null;
}

export interface AccountUpdate {
  name?: string;
  broker?: Broker;
  tax_treatment?: string | null;
}
