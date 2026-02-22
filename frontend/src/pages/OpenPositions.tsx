import { useMemo, useState } from "react";
import { usePositions } from "@/hooks/usePositions";
import { useAccounts } from "@/hooks/useAccounts";
import { usePrices } from "@/hooks/usePrices";
import { useAlerts } from "@/hooks/useAlerts";
import { useSettings } from "@/contexts/SettingsContext";
import { useCreatePosition } from "@/hooks/useCreatePosition";
import { useClosePosition } from "@/hooks/useClosePosition";
import { useRollPosition } from "@/hooks/useRollPosition";
import { useExportCsv } from "@/hooks/useExportCsv";
import PositionsTable, {
  openPositionColumns,
} from "@/components/PositionsTable";
import AddPositionDialog from "@/components/AddPositionDialog";
import ClosePositionDialog from "@/components/ClosePositionDialog";
import RollPositionDialog from "@/components/RollPositionDialog";
import AlertBanner from "@/components/AlertBanner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { PositionCreateBody, PositionCloseBody, PositionRollBody, PositionFilters } from "@/lib/api";
import type { Position, PositionType } from "@/types/position";

export default function OpenPositions() {
  const [tickerSearch, setTickerSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<PositionType | "ALL">("ALL");
  const [accountFilter, setAccountFilter] = useState<string>("ALL");
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");

  const filters: PositionFilters = {
    status: "OPEN",
    ...(tickerSearch ? { ticker: tickerSearch.toUpperCase() } : {}),
    ...(typeFilter !== "ALL" ? { type: typeFilter } : {}),
    ...(accountFilter !== "ALL" ? { account_id: accountFilter } : {}),
    ...(dateStart ? { expiration_start: dateStart } : {}),
    ...(dateEnd ? { expiration_end: dateEnd } : {}),
  };

  const { data: positions, isLoading, error } = usePositions(filters);
  const { data: accounts } = useAccounts();
  const { settings } = useSettings();
  const createPosition = useCreatePosition();
  const closePositionMutation = useClosePosition();
  const rollPositionMutation = useRollPosition();
  const { exportCsv, isExporting } = useExportCsv();

  // Collect distinct tickers from open positions for price fetching
  const tickers = useMemo(() => {
    if (!positions) return [];
    return [...new Set(positions.map((p) => p.ticker))];
  }, [positions]);

  const { data: priceData } = usePrices(tickers);

  // Build a lookup map: ticker -> TickerPrice
  const priceMap = useMemo(() => {
    if (!priceData?.prices) return {};
    return Object.fromEntries(priceData.prices.map((p) => [p.ticker, p]));
  }, [priceData]);

  const { alerts, dismiss, dismissAll } = useAlerts(positions, priceMap, settings);

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [closeDialogOpen, setCloseDialogOpen] = useState(false);
  const [closingPosition, setClosingPosition] = useState<Position | null>(null);
  const [rollDialogOpen, setRollDialogOpen] = useState(false);
  const [rollingPosition, setRollingPosition] = useState<Position | null>(null);

  const accountNames = useMemo(() => {
    if (!accounts) return {};
    return Object.fromEntries(accounts.map((a) => [a.id, a.name]));
  }, [accounts]);

  const columns = useMemo(
    () =>
      openPositionColumns({
        accountNames,
        prices: priceMap,
        nearStrikeThreshold: settings.nearStrikeThreshold,
        stalePriceMinutes: settings.stalePriceMinutes,
        onClose: (position) => {
          setClosingPosition(position);
          setCloseDialogOpen(true);
        },
        onRoll: (position) => {
          setRollingPosition(position);
          setRollDialogOpen(true);
        },
      }),
    [accountNames, priceMap, settings.nearStrikeThreshold, settings.stalePriceMinutes]
  );

  function handleAddSubmit(data: PositionCreateBody) {
    createPosition.mutate(data, {
      onSuccess: () => {
        setAddDialogOpen(false);
      },
    });
  }

  function handleCloseSubmit(id: string, body: PositionCloseBody) {
    closePositionMutation.mutate(
      { id, body },
      {
        onSuccess: () => {
          setCloseDialogOpen(false);
          setClosingPosition(null);
        },
      }
    );
  }

  function handleRollSubmit(id: string, body: PositionRollBody) {
    rollPositionMutation.mutate(
      { id, body },
      {
        onSuccess: () => {
          setRollDialogOpen(false);
          setRollingPosition(null);
        },
      }
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Open Positions</h1>
          <p className="text-muted-foreground mt-1">
            Track your active option positions
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => exportCsv({ status: "OPEN" })}
            disabled={isExporting}
          >
            {isExporting ? "Exporting..." : "Export CSV"}
          </Button>
          <Button onClick={() => setAddDialogOpen(true)}>Add Position</Button>
        </div>
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
          <label className="text-sm font-medium mb-1 block">Exp. From</label>
          <Input
            type="date"
            value={dateStart}
            onChange={(e) => setDateStart(e.target.value)}
          />
        </div>
        <div className="w-40">
          <label className="text-sm font-medium mb-1 block">Exp. To</label>
          <Input
            type="date"
            value={dateEnd}
            onChange={(e) => setDateEnd(e.target.value)}
          />
        </div>
      </div>

      <div className="mt-4">
        <AlertBanner alerts={alerts} onDismiss={dismiss} onDismissAll={dismissAll} />
      </div>

      <div className="mt-4">
        {isLoading && (
          <p className="text-muted-foreground">Loading positions...</p>
        )}
        {error && (
          <p className="text-sm text-destructive">Failed to load positions</p>
        )}
        {positions && positions.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center rounded-md border border-dashed py-12">
            <p className="text-muted-foreground">
              No open positions yet. Add your first position to get started.
            </p>
          </div>
        )}
        {positions && positions.length > 0 && (
          <PositionsTable
            data={positions}
            columns={columns}
            storageKey="wheelhouse_open_col_vis"
          />
        )}
      </div>

      <AddPositionDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        accounts={accounts ?? []}
        onSubmit={handleAddSubmit}
        submitting={createPosition.isPending}
        error={createPosition.error?.message ?? null}
      />

      <ClosePositionDialog
        open={closeDialogOpen}
        onOpenChange={(open) => {
          setCloseDialogOpen(open);
          if (!open) setClosingPosition(null);
        }}
        position={closingPosition}
        onSubmit={handleCloseSubmit}
        submitting={closePositionMutation.isPending}
        error={closePositionMutation.error?.message ?? null}
      />

      <RollPositionDialog
        open={rollDialogOpen}
        onOpenChange={(open) => {
          setRollDialogOpen(open);
          if (!open) setRollingPosition(null);
        }}
        position={rollingPosition}
        accounts={accounts ?? []}
        onSubmit={handleRollSubmit}
        submitting={rollPositionMutation.isPending}
        error={rollPositionMutation.error?.message ?? null}
      />
    </div>
  );
}
