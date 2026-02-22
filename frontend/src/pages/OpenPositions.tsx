import { useMemo } from "react";
import { usePositions } from "@/hooks/usePositions";
import { useAccounts } from "@/hooks/useAccounts";
import PositionsTable, {
  openPositionColumns,
} from "@/components/PositionsTable";

export default function OpenPositions() {
  const { data: positions, isLoading, error } = usePositions({ status: "OPEN" });
  const { data: accounts } = useAccounts();

  const accountNames = useMemo(() => {
    if (!accounts) return {};
    return Object.fromEntries(accounts.map((a) => [a.id, a.name]));
  }, [accounts]);

  const columns = useMemo(() => openPositionColumns(accountNames), [accountNames]);

  return (
    <div>
      <h1 className="text-2xl font-bold">Open Positions</h1>
      <p className="text-muted-foreground mt-1">
        Track your active option positions
      </p>

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
    </div>
  );
}
