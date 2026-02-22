import { useState } from "react";
import { useDashboardSummary } from "@/hooks/useDashboardSummary";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import type { DashboardFilters } from "@/lib/api";
import type { Position } from "@/types/position";

const currencyFmt = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

function formatDate(dateStr: string) {
  return new Date(dateStr + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function SummaryCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-4 w-32" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-24" />
      </CardContent>
    </Card>
  );
}

function UpcomingExpirationsSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-4 w-48" />
      </CardHeader>
      <CardContent className="space-y-3">
        <Skeleton className="h-5 w-full" />
        <Skeleton className="h-5 w-full" />
        <Skeleton className="h-5 w-3/4" />
      </CardContent>
    </Card>
  );
}

function UpcomingExpirationsCard({
  positions,
}: {
  positions: Position[];
}) {
  return (
    <Card className="col-span-full">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Upcoming Expirations (Next 7 Days)
        </CardTitle>
      </CardHeader>
      <CardContent>
        {positions.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            No positions expiring in the next 7 days.
          </p>
        ) : (
          <div className="space-y-2">
            {positions.map((p) => (
              <div
                key={p.id}
                className="flex items-center justify-between rounded-md border px-4 py-2 text-sm"
              >
                <div className="flex items-center gap-3">
                  <span className="font-semibold">{p.ticker}</span>
                  <span className="text-muted-foreground">
                    {p.type === "COVERED_CALL" ? "CC" : "CSP"}
                  </span>
                  <span className="text-muted-foreground">
                    {p.contracts}x @ {currencyFmt.format(p.strike_price)}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-muted-foreground">
                    Expires {formatDate(p.expiration_date)}
                  </span>
                  <span className="font-medium">
                    {p.dte} DTE
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");

  const filters: DashboardFilters = {
    ...(dateStart ? { start: dateStart } : {}),
    ...(dateEnd ? { end: dateEnd } : {}),
  };

  const { data: summary, isLoading, error } = useDashboardSummary(filters);

  return (
    <div>
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Portfolio overview and metrics
        </p>
      </div>

      <div className="mt-4 flex flex-wrap items-end gap-3">
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

      {error && (
        <p className="text-sm text-destructive mt-4">
          Failed to load dashboard data
        </p>
      )}

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          <>
            <SummaryCardSkeleton />
            <SummaryCardSkeleton />
            <SummaryCardSkeleton />
            <UpcomingExpirationsSkeleton />
          </>
        ) : summary ? (
          <>
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Premium Collected
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">
                  {currencyFmt.format(summary.total_premium_collected)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Premium MTD
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">
                  {currencyFmt.format(summary.premium_mtd)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Open Position Count
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">
                  {summary.open_position_count}
                </p>
              </CardContent>
            </Card>

            <UpcomingExpirationsCard
              positions={summary.upcoming_expirations}
            />
          </>
        ) : null}
      </div>
    </div>
  );
}
