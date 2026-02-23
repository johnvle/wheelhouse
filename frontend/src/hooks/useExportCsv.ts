import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { exportPositionsCsv, type ExportFilters } from "@/lib/api";

export function useExportCsv() {
  const { session } = useAuth();
  const token = session?.access_token ?? null;
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function exportCsv(filters: ExportFilters) {
    setIsExporting(true);
    setError(null);
    try {
      await exportPositionsCsv(filters, token);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Export failed";
      setError(message);
    } finally {
      setIsExporting(false);
    }
  }

  return { exportCsv, isExporting, error };
}
