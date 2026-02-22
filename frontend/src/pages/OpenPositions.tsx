import { useMemo, useState } from "react";
import { usePositions } from "@/hooks/usePositions";
import { useAccounts } from "@/hooks/useAccounts";
import { useCreatePosition } from "@/hooks/useCreatePosition";
import { useClosePosition } from "@/hooks/useClosePosition";
import PositionsTable, {
  openPositionColumns,
} from "@/components/PositionsTable";
import AddPositionDialog from "@/components/AddPositionDialog";
import ClosePositionDialog from "@/components/ClosePositionDialog";
import { Button } from "@/components/ui/button";
import type { PositionCreateBody, PositionCloseBody } from "@/lib/api";
import type { Position } from "@/types/position";

export default function OpenPositions() {
  const { data: positions, isLoading, error } = usePositions({ status: "OPEN" });
  const { data: accounts } = useAccounts();
  const createPosition = useCreatePosition();
  const closePositionMutation = useClosePosition();

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [closeDialogOpen, setCloseDialogOpen] = useState(false);
  const [closingPosition, setClosingPosition] = useState<Position | null>(null);

  const accountNames = useMemo(() => {
    if (!accounts) return {};
    return Object.fromEntries(accounts.map((a) => [a.id, a.name]));
  }, [accounts]);

  const columns = useMemo(
    () =>
      openPositionColumns({
        accountNames,
        onClose: (position) => {
          setClosingPosition(position);
          setCloseDialogOpen(true);
        },
      }),
    [accountNames]
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
    </div>
  );
}
