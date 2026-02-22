import { useMemo, useState } from "react";
import { usePositions } from "@/hooks/usePositions";
import { useAccounts } from "@/hooks/useAccounts";
import PositionsTable, {
  closedPositionColumns,
} from "@/components/PositionsTable";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { PositionFilters } from "@/lib/api";
import type { PositionType, PositionOutcome } from "@/types/position";

export default function History() {
  const [tickerSearch, setTickerSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<PositionType | "ALL">("ALL");
  const [accountFilter, setAccountFilter] = useState<string>("ALL");
  const [outcomeFilter, setOutcomeFilter] = useState<PositionOutcome | "ALL">(
    "ALL"
  );
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");

  const filters: PositionFilters = {
    status: "CLOSED",
    ...(tickerSearch ? { ticker: tickerSearch.toUpperCase() } : {}),
    ...(typeFilter !== "ALL" ? { type: typeFilter } : {}),
    ...(accountFilter !== "ALL" ? { account_id: accountFilter } : {}),
    ...(dateStart ? { expiration_start: dateStart } : {}),
    ...(dateEnd ? { expiration_end: dateEnd } : {}),
  };

  const { data: positions, isLoading, error } = usePositions(filters);
  const { data: accounts } = useAccounts();

  const accountNames = useMemo(() => {
    if (!accounts) return {};
    return Object.fromEntries(accounts.map((a) => [a.id, a.name]));
  }, [accounts]);

  // Client-side outcome filter (backend doesn't support outcome query param)
  const filteredPositions = useMemo(() => {
    if (!positions) return [];
    if (outcomeFilter === "ALL") return positions;
    return positions.filter((p) => p.outcome === outcomeFilter);
  }, [positions, outcomeFilter]);

  const columns = useMemo(
    () => closedPositionColumns({ accountNames }),
    [accountNames]
  );

  return (
    <div>
      <div>
        <h1 className="text-2xl font-bold">History</h1>
        <p className="text-muted-foreground mt-1">
          Review your closed positions
        </p>
      </div>

      <div className="mt-4 flex flex-wrap items-end gap-3">
        <div className="w-40">
          <label className="text-sm font-medium mb-1 block">Ticker</label>
          <Input
            placeholder="Search ticker..."
            value={tickerSearch}
            onChange={(e) => setTickerSearch(e.target.value.toUpperCase())}
          />
        </div>
        <div className="w-40">
          <label className="text-sm font-medium mb-1 block">Type</label>
          <Select
            value={typeFilter}
            onValueChange={(v) => setTypeFilter(v as PositionType | "ALL")}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Types</SelectItem>
              <SelectItem value="COVERED_CALL">Covered Call</SelectItem>
              <SelectItem value="CASH_SECURED_PUT">Cash Secured Put</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="w-40">
          <label className="text-sm font-medium mb-1 block">Account</label>
          <Select
            value={accountFilter}
            onValueChange={setAccountFilter}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Accounts</SelectItem>
              {(accounts ?? []).map((a) => (
                <SelectItem key={a.id} value={a.id}>
                  {a.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-40">
          <label className="text-sm font-medium mb-1 block">Outcome</label>
          <Select
            value={outcomeFilter}
            onValueChange={(v) =>
              setOutcomeFilter(v as PositionOutcome | "ALL")
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Outcomes</SelectItem>
              <SelectItem value="EXPIRED">Expired</SelectItem>
              <SelectItem value="ASSIGNED">Assigned</SelectItem>
              <SelectItem value="CLOSED_EARLY">Closed Early</SelectItem>
              <SelectItem value="ROLLED">Rolled</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="w-40">
          <label className="text-sm font-medium mb-1 block">From</label>
          <Input
            type="date"
            value={dateStart}
            onChange={(e) => setDateStart(e.target.value)}
          />
        </div>
        <div className="w-40">
          <label className="text-sm font-medium mb-1 block">To</label>
          <Input
            type="date"
            value={dateEnd}
            onChange={(e) => setDateEnd(e.target.value)}
          />
        </div>
      </div>

      <div className="mt-6">
        {isLoading && (
          <p className="text-muted-foreground">Loading positions...</p>
        )}
        {error && (
          <p className="text-sm text-destructive">
            Failed to load positions
          </p>
        )}
        {filteredPositions.length === 0 && !isLoading && !error && (
          <div className="flex flex-col items-center justify-center rounded-md border border-dashed py-12">
            <p className="text-muted-foreground">
              No closed positions found. Positions will appear here after you
              close them.
            </p>
          </div>
        )}
        {filteredPositions.length > 0 && (
          <PositionsTable data={filteredPositions} columns={columns} />
        )}
      </div>
    </div>
  );
}
