import { useState, useEffect, type FormEvent } from "react";
import type { Account } from "@/types/account";
import type { PositionType } from "@/types/position";
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
import type { PositionCreateBody } from "@/lib/api";

interface AddPositionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accounts: Account[];
  onSubmit: (data: PositionCreateBody) => void;
  submitting: boolean;
  error?: string | null;
}

export default function AddPositionDialog({
  open,
  onOpenChange,
  accounts,
  onSubmit,
  submitting,
  error,
}: AddPositionDialogProps) {
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
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (open) {
      setAccountId(accounts.length > 0 ? accounts[0].id : "");
      setTicker("");
      setType("COVERED_CALL");
      setOpenDate(new Date().toISOString().slice(0, 10));
      setExpirationDate("");
      setStrikePrice("");
      setContracts("");
      setPremiumPerShare("");
      setMultiplier("100");
      setOpenFees("");
      setNotes("");
      setTags("");
      setValidationErrors({});
    }
  }, [open, accounts]);

  function validate(): boolean {
    const errors: Record<string, string> = {};
    if (!accountId) errors.accountId = "Account is required";
    if (!ticker.trim()) errors.ticker = "Ticker is required";
    if (!openDate) errors.openDate = "Open date is required";
    if (!expirationDate) errors.expirationDate = "Expiration date is required";
    if (!strikePrice || Number(strikePrice) <= 0)
      errors.strikePrice = "Strike price must be greater than 0";
    if (!contracts || Number(contracts) <= 0 || !Number.isInteger(Number(contracts)))
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

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    const body: PositionCreateBody = {
      account_id: accountId,
      ticker: ticker.trim().toUpperCase(),
      type,
      open_date: openDate,
      expiration_date: expirationDate,
      strike_price: Number(strikePrice),
      contracts: Number(contracts),
      premium_per_share: Number(premiumPerShare),
    };

    const mult = Number(multiplier);
    if (mult && mult !== 100) body.multiplier = mult;

    const fees = Number(openFees);
    if (openFees && fees >= 0) body.open_fees = fees;

    if (notes.trim()) body.notes = notes.trim();

    if (tags.trim()) {
      body.tags = tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
    }

    onSubmit(body);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Add Position</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Account */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="pos-account">Account</Label>
            <Select value={accountId} onValueChange={setAccountId}>
              <SelectTrigger id="pos-account">
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
              <p className="text-sm text-destructive">{validationErrors.accountId}</p>
            )}
          </div>

          {/* Ticker & Type row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="pos-ticker">Ticker</Label>
              <Input
                id="pos-ticker"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                placeholder="e.g., AAPL"
              />
              {validationErrors.ticker && (
                <p className="text-sm text-destructive">{validationErrors.ticker}</p>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="pos-type">Type</Label>
              <Select value={type} onValueChange={(v) => setType(v as PositionType)}>
                <SelectTrigger id="pos-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="COVERED_CALL">Covered Call</SelectItem>
                  <SelectItem value="CASH_SECURED_PUT">Cash Secured Put</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Dates row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="pos-open-date">Open Date</Label>
              <Input
                id="pos-open-date"
                type="date"
                value={openDate}
                onChange={(e) => setOpenDate(e.target.value)}
              />
              {validationErrors.openDate && (
                <p className="text-sm text-destructive">{validationErrors.openDate}</p>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="pos-exp-date">Expiration Date</Label>
              <Input
                id="pos-exp-date"
                type="date"
                value={expirationDate}
                onChange={(e) => setExpirationDate(e.target.value)}
              />
              {validationErrors.expirationDate && (
                <p className="text-sm text-destructive">{validationErrors.expirationDate}</p>
              )}
            </div>
          </div>

          {/* Strike / Contracts / Premium row */}
          <div className="grid grid-cols-3 gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="pos-strike">Strike Price</Label>
              <Input
                id="pos-strike"
                type="number"
                step="0.01"
                min="0"
                value={strikePrice}
                onChange={(e) => setStrikePrice(e.target.value)}
                placeholder="0.00"
              />
              {validationErrors.strikePrice && (
                <p className="text-sm text-destructive">{validationErrors.strikePrice}</p>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="pos-contracts">Contracts</Label>
              <Input
                id="pos-contracts"
                type="number"
                step="1"
                min="1"
                value={contracts}
                onChange={(e) => setContracts(e.target.value)}
                placeholder="1"
              />
              {validationErrors.contracts && (
                <p className="text-sm text-destructive">{validationErrors.contracts}</p>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="pos-premium">Premium/Share</Label>
              <Input
                id="pos-premium"
                type="number"
                step="0.01"
                min="0"
                value={premiumPerShare}
                onChange={(e) => setPremiumPerShare(e.target.value)}
                placeholder="0.00"
              />
              {validationErrors.premiumPerShare && (
                <p className="text-sm text-destructive">{validationErrors.premiumPerShare}</p>
              )}
            </div>
          </div>

          {/* Optional: Multiplier & Fees row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="pos-multiplier">Multiplier (optional)</Label>
              <Input
                id="pos-multiplier"
                type="number"
                step="1"
                min="1"
                value={multiplier}
                onChange={(e) => setMultiplier(e.target.value)}
              />
              {validationErrors.multiplier && (
                <p className="text-sm text-destructive">{validationErrors.multiplier}</p>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="pos-fees">Open Fees (optional)</Label>
              <Input
                id="pos-fees"
                type="number"
                step="0.01"
                min="0"
                value={openFees}
                onChange={(e) => setOpenFees(e.target.value)}
                placeholder="0.00"
              />
              {validationErrors.openFees && (
                <p className="text-sm text-destructive">{validationErrors.openFees}</p>
              )}
            </div>
          </div>

          {/* Notes */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="pos-notes">Notes (optional)</Label>
            <Textarea
              id="pos-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Any notes about this trade..."
              rows={2}
            />
          </div>

          {/* Tags */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="pos-tags">Tags (optional)</Label>
            <Input
              id="pos-tags"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="e.g., earnings, weekly, high-iv"
            />
            <p className="text-xs text-muted-foreground">Comma-separated</p>
          </div>

          {/* Error */}
          {error && <p className="text-sm text-destructive">{error}</p>}

          <Button type="submit" disabled={submitting}>
            {submitting ? "Adding..." : "Add Position"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
