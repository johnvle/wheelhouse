import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { useState } from "react";
import type { Position } from "@/types/position";
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
}

export function openPositionColumns(
  accountNames?: Record<string, string>
): ColumnDef<Position>[] {
  return [
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
  ];
}

export default function PositionsTable({
  data,
  columns,
}: PositionsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
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
  );
}
