import { useMemo, useState } from "react";
import { usePositions } from "@/hooks/usePositions";
import { useAccounts } from "@/hooks/useAccounts";
import { useCreatePosition } from "@/hooks/useCreatePosition";
import PositionsTable, {
  openPositionColumns,
} from "@/components/PositionsTable";
import AddPositionDialog from "@/components/AddPositionDialog";
import { Button } from "@/components/ui/button";
import type { PositionCreateBody } from "@/lib/api";

export default function OpenPositions() {
  const { data: positions, isLoading, error } = usePositions({ status: "OPEN" });
  const { data: accounts } = useAccounts();
  const createPosition = useCreatePosition();

  const [dialogOpen, setDialogOpen] = useState(false);

  const accountNames = useMemo(() => {
    if (!accounts) return {};
    return Object.fromEntries(accounts.map((a) => [a.id, a.name]));
  }, [accounts]);

  const columns = useMemo(() => openPositionColumns(accountNames), [accountNames]);

  function handleSubmit(data: PositionCreateBody) {
    createPosition.mutate(data, {
      onSuccess: () => {
        setDialogOpen(false);
      },
    });
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
        <Button onClick={() => setDialogOpen(true)}>Add Position</Button>
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
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        accounts={accounts ?? []}
        onSubmit={handleSubmit}
        submitting={createPosition.isPending}
        error={createPosition.error?.message ?? null}
      />
    </div>
  );
}
