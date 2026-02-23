import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
  type VisibilityState,
} from "@tanstack/react-table";
import { useState, useEffect } from "react";
import type { Position } from "@/types/position";
import type { TickerPrice } from "@/types/price";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const currencyFmt = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

const pctFmt = new Intl.NumberFormat("en-US", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

interface PositionsTableProps {
  data: Position[];
  columns: ColumnDef<Position>[];
  storageKey?: string;
}

interface OpenPositionColumnOptions {
  accountNames?: Record<string, string>;
  prices?: Record<string, TickerPrice>;
  nearStrikeThreshold?: number;
  stalePriceMinutes?: number;
  onClose?: (position: Position) => void;
  onRoll?: (position: Position) => void;
}

/** Check if a price is stale (last fetched > threshold minutes ago). */
function isPriceStale(price: TickerPrice, stalePriceMinutes = 5): boolean {
  if (!price.last_fetched) return true;
  const fetched = new Date(price.last_fetched).getTime();
  return Date.now() - fetched > stalePriceMinutes * 60 * 1000;
}

/** Check if price is near the strike for alerting. */
function isNearStrike(
  position: Position,
  currentPrice: number | null,
  threshold = 0.05
): boolean {
  if (currentPrice == null) return false;
  const strike = position.strike_price;
  if (position.type === "COVERED_CALL") {
    return currentPrice >= strike * (1 - threshold);
  }
  // CASH_SECURED_PUT
  return currentPrice <= strike * (1 + threshold);
}

export function openPositionColumns(
  accountNamesOrOptions?: Record<string, string> | OpenPositionColumnOptions
): ColumnDef<Position>[] {
  // Support both old signature (just accountNames) and new options object
  let accountNames: Record<string, string> | undefined;
  let prices: Record<string, TickerPrice> | undefined;
  let nearStrikeThreshold = 0.05;
  let stalePriceMinutes = 5;
  let onClose: ((position: Position) => void) | undefined;
  let onRoll: ((position: Position) => void) | undefined;

  if (
    accountNamesOrOptions &&
    typeof accountNamesOrOptions === "object" &&
    ("onClose" in accountNamesOrOptions ||
      "onRoll" in accountNamesOrOptions ||
      "prices" in accountNamesOrOptions)
  ) {
    accountNames = accountNamesOrOptions.accountNames;
    prices = accountNamesOrOptions.prices;
    nearStrikeThreshold = accountNamesOrOptions.nearStrikeThreshold ?? 0.05;
    stalePriceMinutes = accountNamesOrOptions.stalePriceMinutes ?? 5;
    onClose = accountNamesOrOptions.onClose;
    onRoll = accountNamesOrOptions.onRoll;
  } else {
    accountNames = accountNamesOrOptions as Record<string, string> | undefined;
  }

  const cols: ColumnDef<Position>[] = [
    {
      accessorKey: "account_id",
      header: "Account",
      cell: ({ getValue }) => {
        const id = getValue<string>();
        return accountNames?.[id] ?? "—";
      },
    },
    {
      accessorKey: "ticker",
      header: "Ticker",
    },
    {
      accessorKey: "type",
      header: "Type",
      cell: ({ getValue }) => {
        const v = getValue<string>();
        return v === "COVERED_CALL" ? "CC" : "CSP";
      },
    },
    {
      accessorKey: "strike_price",
      header: "Strike",
      cell: ({ getValue }) => currencyFmt.format(getValue<number>()),
    },
    {
      accessorKey: "contracts",
      header: "Contracts",
    },
    {
      accessorKey: "premium_per_share",
      header: "Prem/Share",
      cell: ({ getValue }) => currencyFmt.format(getValue<number>()),
    },
    {
      accessorKey: "premium_total",
      header: "Premium Total",
      cell: ({ getValue }) => currencyFmt.format(getValue<number>()),
    },
    {
      accessorKey: "collateral",
      header: "Collateral",
      cell: ({ getValue }) => currencyFmt.format(getValue<number>()),
    },
    {
      accessorKey: "open_date",
      header: "Open Date",
    },
    {
      accessorKey: "expiration_date",
      header: "Expiration",
    },
    {
      accessorKey: "dte",
      header: "DTE",
    },
    {
      accessorKey: "annualized_roc",
      header: "Ann. ROC",
      cell: ({ getValue }) => pctFmt.format(getValue<number>()),
    },
    {
      id: "current_price",
      header: "Current Price",
      accessorFn: (row) => prices?.[row.ticker]?.current_price ?? null,
      cell: ({ row }) => {
        const ticker = row.original.ticker;
        const tickerPrice = prices?.[ticker];
        if (!tickerPrice || tickerPrice.current_price == null) {
          return <span className="text-muted-foreground">—</span>;
        }

        const stale = isPriceStale(tickerPrice, stalePriceMinutes);
        const nearStrike = isNearStrike(row.original, tickerPrice.current_price, nearStrikeThreshold);
        const changePct = tickerPrice.change_percent;
        const changeColor =
          changePct != null && changePct >= 0
            ? "text-green-600"
            : "text-red-600";

        return (
          <span
            className={nearStrike ? "rounded bg-yellow-100 px-1 font-semibold" : ""}
            title={
              nearStrike
                ? "Price near strike"
                : undefined
            }
          >
            {currencyFmt.format(tickerPrice.current_price)}
            {changePct != null && (
              <span className={`ml-1 text-xs ${changeColor}`}>
                {changePct >= 0 ? "+" : ""}
                {changePct.toFixed(2)}%
              </span>
            )}
            {stale && (
              <span
                className="ml-1 text-xs text-orange-500"
                title={`Price data may be stale (>${stalePriceMinutes} min old)`}
              >
                !
              </span>
            )}
          </span>
        );
      },
    },
  ];

  if (onClose || onRoll) {
    const closeFn = onClose;
    const rollFn = onRoll;
    cols.push({
      id: "actions",
      header: "",
      enableSorting: false,
      enableHiding: false,
      cell: ({ row }) => (
        <div className="flex gap-1">
          {closeFn && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => closeFn(row.original)}
            >
              Close
            </Button>
          )}
          {rollFn && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => rollFn(row.original)}
            >
              Roll
            </Button>
          )}
        </div>
      ),
    });
  }

  return cols;
}

interface ClosedPositionColumnOptions {
  accountNames?: Record<string, string>;
}

export function closedPositionColumns(
  options?: ClosedPositionColumnOptions
): ColumnDef<Position>[] {
  const accountNames = options?.accountNames;

  return [
    {
      accessorKey: "ticker",
      header: "Ticker",
    },
    {
      accessorKey: "type",
      header: "Type",
      cell: ({ getValue }) => {
        const v = getValue<string>();
        return v === "COVERED_CALL" ? "CC" : "CSP";
      },
    },
    {
      accessorKey: "account_id",
      header: "Account",
      cell: ({ getValue }) => {
        const id = getValue<string>();
        return accountNames?.[id] ?? "—";
      },
    },
    {
      accessorKey: "strike_price",
      header: "Strike",
      cell: ({ getValue }) => currencyFmt.format(getValue<number>()),
    },
    {
      accessorKey: "contracts",
      header: "Contracts",
    },
    {
      accessorKey: "premium_total",
      header: "Premium Total",
      cell: ({ getValue }) => currencyFmt.format(getValue<number>()),
    },
    {
      accessorKey: "premium_net",
      header: "Premium Net",
      cell: ({ getValue }) => currencyFmt.format(getValue<number>()),
    },
    {
      accessorKey: "open_date",
      header: "Open Date",
    },
    {
      accessorKey: "close_date",
      header: "Close Date",
    },
    {
      accessorKey: "outcome",
      header: "Outcome",
      cell: ({ row }) => {
        const outcome = row.original.outcome;
        const rollGroupId = row.original.roll_group_id;
        if (outcome === "ROLLED" && rollGroupId) {
          return (
            <span className="inline-flex items-center gap-1">
              {outcome}
              <span
                className="inline-block h-2 w-2 rounded-full bg-blue-500"
                title={`Roll group: ${rollGroupId.slice(0, 8)}`}
              />
            </span>
          );
        }
        return outcome ?? "—";
      },
    },
    {
      accessorKey: "annualized_roc",
      header: "Ann. ROC",
      cell: ({ getValue }) => pctFmt.format(getValue<number>()),
    },
  ];
}

function loadColumnVisibility(key: string): VisibilityState {
  try {
    const raw = localStorage.getItem(key);
    if (raw) return JSON.parse(raw);
  } catch {
    // ignore
  }
  return {};
}

function saveColumnVisibility(key: string, state: VisibilityState) {
  localStorage.setItem(key, JSON.stringify(state));
}

export default function PositionsTable({
  data,
  columns,
  storageKey,
}: PositionsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>(
    () => (storageKey ? loadColumnVisibility(storageKey) : {})
  );

  useEffect(() => {
    if (storageKey) {
      saveColumnVisibility(storageKey, columnVisibility);
    }
  }, [storageKey, columnVisibility]);

  const table = useReactTable({
    data,
    columns,
    state: { sorting, columnVisibility },
    onSortingChange: setSorting,
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div>
      {storageKey && (
        <div className="flex justify-end mb-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                Columns
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              {table
                .getAllColumns()
                .filter((col) => col.getCanHide())
                .map((col) => (
                  <DropdownMenuCheckboxItem
                    key={col.id}
                    checked={col.getIsVisible()}
                    onCheckedChange={(v) => col.toggleVisibility(!!v)}
                  >
                    {typeof col.columnDef.header === "string"
                      ? col.columnDef.header
                      : col.id}
                  </DropdownMenuCheckboxItem>
                ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      )}
      <div className="overflow-x-auto rounded-md border">
        <Table>
          <TableHeader className="sticky top-0 z-10 bg-background">
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className="cursor-pointer select-none whitespace-nowrap"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                    {{
                      asc: " \u2191",
                      desc: " \u2193",
                    }[header.column.getIsSorted() as string] ?? ""}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center text-muted-foreground"
                >
                  No positions found.
                </TableCell>
              </TableRow>
            ) : (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="whitespace-nowrap">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
