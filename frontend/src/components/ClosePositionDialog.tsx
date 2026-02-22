import { useState, useEffect, type FormEvent } from "react";
import type { Position } from "@/types/position";
import type { PositionCloseBody } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type CloseOutcome = "EXPIRED" | "ASSIGNED" | "CLOSED_EARLY";

interface ClosePositionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  position: Position | null;
  onSubmit: (id: string, body: PositionCloseBody) => void;
  submitting: boolean;
  error?: string | null;
}

export default function ClosePositionDialog({
  open,
  onOpenChange,
  position,
  onSubmit,
  submitting,
  error,
}: ClosePositionDialogProps) {
  const [outcome, setOutcome] = useState<CloseOutcome>("EXPIRED");
  const [closeDate, setCloseDate] = useState("");
  const [closePricePerShare, setClosePricePerShare] = useState("");
  const [closeFees, setCloseFees] = useState("");
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (open) {
      setOutcome("EXPIRED");
      setCloseDate(new Date().toISOString().slice(0, 10));
      setClosePricePerShare("");
      setCloseFees("");
      setValidationErrors({});
    }
  }, [open]);

  function validate(): boolean {
    const errors: Record<string, string> = {};
    if (!closeDate) errors.closeDate = "Close date is required";
    if (closePricePerShare && Number(closePricePerShare) < 0)
      errors.closePricePerShare = "Close price cannot be negative";
    if (closeFees && Number(closeFees) < 0)
      errors.closeFees = "Close fees cannot be negative";
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate() || !position) return;

    const body: PositionCloseBody = {
      outcome,
      close_date: closeDate,
    };

    if (closePricePerShare) {
      body.close_price_per_share = Number(closePricePerShare);
    }

    if (closeFees) {
      body.close_fees = Number(closeFees);
    }

    onSubmit(position.id, body);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            Close Position{position ? ` — ${position.ticker}` : ""}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Outcome */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="close-outcome">Outcome</Label>
            <Select value={outcome} onValueChange={(v) => setOutcome(v as CloseOutcome)}>
              <SelectTrigger id="close-outcome">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="EXPIRED">Expired</SelectItem>
                <SelectItem value="ASSIGNED">Assigned</SelectItem>
                <SelectItem value="CLOSED_EARLY">Closed Early</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Close Date */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="close-date">Close Date</Label>
            <Input
              id="close-date"
              type="date"
              value={closeDate}
              onChange={(e) => setCloseDate(e.target.value)}
            />
            {validationErrors.closeDate && (
              <p className="text-sm text-destructive">{validationErrors.closeDate}</p>
            )}
          </div>

          {/* Close Price & Fees row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="close-price">Close Price/Share (optional)</Label>
              <Input
                id="close-price"
                type="number"
                step="0.01"
                min="0"
                value={closePricePerShare}
                onChange={(e) => setClosePricePerShare(e.target.value)}
                placeholder="0.00"
              />
              {validationErrors.closePricePerShare && (
                <p className="text-sm text-destructive">{validationErrors.closePricePerShare}</p>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="close-fees">Close Fees (optional)</Label>
              <Input
                id="close-fees"
                type="number"
                step="0.01"
                min="0"
                value={closeFees}
                onChange={(e) => setCloseFees(e.target.value)}
                placeholder="0.00"
              />
              {validationErrors.closeFees && (
                <p className="text-sm text-destructive">{validationErrors.closeFees}</p>
              )}
            </div>
          </div>

          {/* Error */}
          {error && <p className="text-sm text-destructive">{error}</p>}

          <Button type="submit" disabled={submitting}>
            {submitting ? "Closing..." : "Close Position"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
