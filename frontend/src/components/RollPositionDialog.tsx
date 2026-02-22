import { useState, useEffect, type FormEvent } from "react";
import type { Position, PositionType } from "@/types/position";
import type { Account } from "@/types/account";
import type { PositionRollBody } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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

interface RollPositionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  position: Position | null;
  accounts: Account[];
  onSubmit: (id: string, body: PositionRollBody) => void;
  submitting: boolean;
  error?: string | null;
}

export default function RollPositionDialog({
  open,
  onOpenChange,
  position,
  accounts,
  onSubmit,
  submitting,
  error,
}: RollPositionDialogProps) {
  const [step, setStep] = useState<1 | 2>(1);

  // Step 1: Close fields
  const [closeDate, setCloseDate] = useState("");
  const [closePricePerShare, setClosePricePerShare] = useState("");
  const [closeFees, setCloseFees] = useState("");

  // Step 2: Open fields (prefilled from old position)
  const [accountId, setAccountId] = useState("");
  const [ticker, setTicker] = useState("");
  const [type, setType] = useState<PositionType>("COVERED_CALL");
  const [openDate, setOpenDate] = useState("");
  const [expirationDate, setExpirationDate] = useState("");
  const [strikePrice, setStrikePrice] = useState("");
  const [contracts, setContracts] = useState("");
  const [premiumPerShare, setPremiumPerShare] = useState("");
  const [multiplier, setMultiplier] = useState("100");
  const [openFees, setOpenFees] = useState("");
  const [notes, setNotes] = useState("");
  const [tags, setTags] = useState("");

  const [validationErrors, setValidationErrors] = useState<
    Record<string, string>
  >({});

  useEffect(() => {
    if (open && position) {
      setStep(1);
      // Step 1 defaults
      setCloseDate(new Date().toISOString().slice(0, 10));
      setClosePricePerShare("");
      setCloseFees("");
      // Step 2 prefilled from old position
      setAccountId(position.account_id);
      setTicker(position.ticker);
      setType(position.type);
      setOpenDate(new Date().toISOString().slice(0, 10));
      setExpirationDate("");
      setStrikePrice("");
      setContracts(String(position.contracts));
      setPremiumPerShare("");
      setMultiplier(String(position.multiplier));
      setOpenFees("");
      setNotes("");
      setTags("");
      setValidationErrors({});
    }
  }, [open, position]);

  function validateStep1(): boolean {
    const errors: Record<string, string> = {};
    if (!closeDate) errors.closeDate = "Close date is required";
    if (closePricePerShare && Number(closePricePerShare) < 0)
      errors.closePricePerShare = "Close price cannot be negative";
    if (closeFees && Number(closeFees) < 0)
      errors.closeFees = "Close fees cannot be negative";
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }

  function validateStep2(): boolean {
    const errors: Record<string, string> = {};
    if (!accountId) errors.accountId = "Account is required";
    if (!ticker.trim()) errors.ticker = "Ticker is required";
    if (!openDate) errors.openDate = "Open date is required";
    if (!expirationDate) errors.expirationDate = "Expiration date is required";
    if (!strikePrice || Number(strikePrice) <= 0)
      errors.strikePrice = "Strike price must be greater than 0";
    if (
      !contracts ||
      Number(contracts) <= 0 ||
      !Number.isInteger(Number(contracts))
    )
      errors.contracts = "Contracts must be a positive integer";
    if (!premiumPerShare || Number(premiumPerShare) < 0)
      errors.premiumPerShare = "Premium per share must be 0 or greater";
    if (multiplier && Number(multiplier) <= 0)
      errors.multiplier = "Multiplier must be greater than 0";
    if (openFees && Number(openFees) < 0)
      errors.openFees = "Open fees cannot be negative";
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }

  function handleNext(e: FormEvent) {
    e.preventDefault();
    if (!validateStep1()) return;
    setValidationErrors({});
    setStep(2);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validateStep2() || !position) return;

    const body: PositionRollBody = {
      close: {
        close_date: closeDate,
      },
      open: {
        account_id: accountId,
        ticker: ticker.trim().toUpperCase(),
        type,
        open_date: openDate,
        expiration_date: expirationDate,
        strike_price: Number(strikePrice),
        contracts: Number(contracts),
        premium_per_share: Number(premiumPerShare),
      },
    };

    if (closePricePerShare) {
      body.close.close_price_per_share = Number(closePricePerShare);
    }
    if (closeFees) {
      body.close.close_fees = Number(closeFees);
    }

    const mult = Number(multiplier);
    if (mult && mult !== 100) body.open.multiplier = mult;

    const fees = Number(openFees);
    if (openFees && fees >= 0) body.open.open_fees = fees;

    if (notes.trim()) body.open.notes = notes.trim();

    if (tags.trim()) {
      body.open.tags = tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
    }

    onSubmit(position.id, body);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            Roll Position{position ? ` — ${position.ticker}` : ""}
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              Step {step} of 2
            </span>
          </DialogTitle>
        </DialogHeader>

        {step === 1 ? (
          <form onSubmit={handleNext} className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">
              Close the existing position with outcome{" "}
              <span className="font-medium">ROLLED</span>.
            </p>

            {/* Close Date */}
            <div className="flex flex-col gap-2">
              <Label htmlFor="roll-close-date">Close Date</Label>
              <Input
                id="roll-close-date"
                type="date"
                value={closeDate}
                onChange={(e) => setCloseDate(e.target.value)}
              />
              {validationErrors.closeDate && (
                <p className="text-sm text-destructive">
                  {validationErrors.closeDate}
                </p>
              )}
            </div>

            {/* Close Price & Fees row */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="roll-close-price">
                  Close Price/Share (optional)
                </Label>
                <Input
                  id="roll-close-price"
                  type="number"
                  step="0.01"
                  min="0"
                  value={closePricePerShare}
                  onChange={(e) => setClosePricePerShare(e.target.value)}
                  placeholder="0.00"
                />
                {validationErrors.closePricePerShare && (
                  <p className="text-sm text-destructive">
                    {validationErrors.closePricePerShare}
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="roll-close-fees">Close Fees (optional)</Label>
                <Input
                  id="roll-close-fees"
                  type="number"
                  step="0.01"
                  min="0"
                  value={closeFees}
                  onChange={(e) => setCloseFees(e.target.value)}
                  placeholder="0.00"
                />
                {validationErrors.closeFees && (
                  <p className="text-sm text-destructive">
                    {validationErrors.closeFees}
                  </p>
                )}
              </div>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Cancel
              </Button>
              <Button type="submit">Next: New Position</Button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">
              Open a new position to replace the rolled one. Fields are
              prefilled from the original position.
            </p>

            {/* Account */}
            <div className="flex flex-col gap-2">
              <Label htmlFor="roll-account">Account</Label>
              <Select value={accountId} onValueChange={setAccountId}>
                <SelectTrigger id="roll-account">
                  <SelectValue placeholder="Select account" />
                </SelectTrigger>
                <SelectContent>
                  {accounts.map((a) => (
                    <SelectItem key={a.id} value={a.id}>
                      {a.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {validationErrors.accountId && (
                <p className="text-sm text-destructive">
                  {validationErrors.accountId}
                </p>
              )}
            </div>

            {/* Ticker & Type row */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="roll-ticker">Ticker</Label>
                <Input
                  id="roll-ticker"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  placeholder="e.g., AAPL"
                />
                {validationErrors.ticker && (
                  <p className="text-sm text-destructive">
                    {validationErrors.ticker}
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="roll-type">Type</Label>
                <Select
                  value={type}
                  onValueChange={(v) => setType(v as PositionType)}
                >
                  <SelectTrigger id="roll-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="COVERED_CALL">Covered Call</SelectItem>
                    <SelectItem value="CASH_SECURED_PUT">
                      Cash Secured Put
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Dates row */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="roll-open-date">Open Date</Label>
                <Input
                  id="roll-open-date"
                  type="date"
                  value={openDate}
                  onChange={(e) => setOpenDate(e.target.value)}
                />
                {validationErrors.openDate && (
                  <p className="text-sm text-destructive">
                    {validationErrors.openDate}
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="roll-exp-date">Expiration Date</Label>
                <Input
                  id="roll-exp-date"
                  type="date"
                  value={expirationDate}
                  onChange={(e) => setExpirationDate(e.target.value)}
                />
                {validationErrors.expirationDate && (
                  <p className="text-sm text-destructive">
                    {validationErrors.expirationDate}
                  </p>
                )}
              </div>
            </div>

            {/* Strike / Contracts / Premium row */}
            <div className="grid grid-cols-3 gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="roll-strike">Strike Price</Label>
                <Input
                  id="roll-strike"
                  type="number"
                  step="0.01"
                  min="0"
                  value={strikePrice}
                  onChange={(e) => setStrikePrice(e.target.value)}
                  placeholder="0.00"
                />
                {validationErrors.strikePrice && (
                  <p className="text-sm text-destructive">
                    {validationErrors.strikePrice}
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="roll-contracts">Contracts</Label>
                <Input
                  id="roll-contracts"
                  type="number"
                  step="1"
                  min="1"
                  value={contracts}
                  onChange={(e) => setContracts(e.target.value)}
                  placeholder="1"
                />
                {validationErrors.contracts && (
                  <p className="text-sm text-destructive">
                    {validationErrors.contracts}
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="roll-premium">Premium/Share</Label>
                <Input
                  id="roll-premium"
                  type="number"
                  step="0.01"
                  min="0"
                  value={premiumPerShare}
                  onChange={(e) => setPremiumPerShare(e.target.value)}
                  placeholder="0.00"
                />
                {validationErrors.premiumPerShare && (
                  <p className="text-sm text-destructive">
                    {validationErrors.premiumPerShare}
                  </p>
                )}
              </div>
            </div>

            {/* Optional: Multiplier & Fees row */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="roll-multiplier">Multiplier (optional)</Label>
                <Input
                  id="roll-multiplier"
                  type="number"
                  step="1"
                  min="1"
                  value={multiplier}
                  onChange={(e) => setMultiplier(e.target.value)}
                />
                {validationErrors.multiplier && (
                  <p className="text-sm text-destructive">
                    {validationErrors.multiplier}
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="roll-open-fees">Open Fees (optional)</Label>
                <Input
                  id="roll-open-fees"
                  type="number"
                  step="0.01"
                  min="0"
                  value={openFees}
                  onChange={(e) => setOpenFees(e.target.value)}
                  placeholder="0.00"
                />
                {validationErrors.openFees && (
                  <p className="text-sm text-destructive">
                    {validationErrors.openFees}
                  </p>
                )}
              </div>
            </div>

            {/* Notes */}
            <div className="flex flex-col gap-2">
              <Label htmlFor="roll-notes">Notes (optional)</Label>
              <Textarea
                id="roll-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Any notes about the new position..."
                rows={2}
              />
            </div>

            {/* Tags */}
            <div className="flex flex-col gap-2">
              <Label htmlFor="roll-tags">Tags (optional)</Label>
              <Input
                id="roll-tags"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="e.g., earnings, weekly, high-iv"
              />
              <p className="text-xs text-muted-foreground">Comma-separated</p>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep(1)}
              >
                Back
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Rolling..." : "Roll Position"}
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
