import { useMemo, useState } from "react";
import { usePositions } from "@/hooks/usePositions";
import { useAccounts } from "@/hooks/useAccounts";
import { usePrices } from "@/hooks/usePrices";
import { useAlerts } from "@/hooks/useAlerts";
import { useCreatePosition } from "@/hooks/useCreatePosition";
import { useClosePosition } from "@/hooks/useClosePosition";
import { useRollPosition } from "@/hooks/useRollPosition";
import PositionsTable, {
  openPositionColumns,
} from "@/components/PositionsTable";
import AddPositionDialog from "@/components/AddPositionDialog";
import ClosePositionDialog from "@/components/ClosePositionDialog";
import RollPositionDialog from "@/components/RollPositionDialog";
import AlertBanner from "@/components/AlertBanner";
import { Button } from "@/components/ui/button";
import type { PositionCreateBody, PositionCloseBody, PositionRollBody } from "@/lib/api";
import type { Position } from "@/types/position";

export default function OpenPositions() {
  const { data: positions, isLoading, error } = usePositions({ status: "OPEN" });
  const { data: accounts } = useAccounts();
  const createPosition = useCreatePosition();
  const closePositionMutation = useClosePosition();
  const rollPositionMutation = useRollPosition();

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

  const { alerts, dismiss, dismissAll } = useAlerts(positions, priceMap);

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
        onClose: (position) => {
          setClosingPosition(position);
          setCloseDialogOpen(true);
        },
        onRoll: (position) => {
          setRollingPosition(position);
          setRollDialogOpen(true);
        },
      }),
    [accountNames, priceMap]
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
        <Button onClick={() => setAddDialogOpen(true)}>Add Position</Button>
      </div>

      <div className="mt-4">
        <AlertBanner alerts={alerts} onDismiss={dismiss} onDismissAll={dismissAll} />
      </div>

      <div className="mt-6">
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
