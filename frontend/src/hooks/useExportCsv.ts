import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { exportPositionsCsv, type ExportFilters } from "@/lib/api";

export function useExportCsv() {
  const { session } = useAuth();
  const token = session?.access_token ?? null;
  const [isExporting, setIsExporting] = useState(false);

  async function exportCsv(filters: ExportFilters) {
    setIsExporting(true);
    try {
      await exportPositionsCsv(filters, token);
    } finally {
      setIsExporting(false);
    }
  }

  return { exportCsv, isExporting };
}
