import { useState, useEffect, type FormEvent } from "react";
import type { Account, Broker } from "@/types/account";
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

interface AccountFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  account?: Account | null;
  onSubmit: (data: { name: string; broker: Broker; tax_treatment?: string }) => void;
  submitting: boolean;
}

export default function AccountFormDialog({
  open,
  onOpenChange,
  account,
  onSubmit,
  submitting,
}: AccountFormDialogProps) {
  const [name, setName] = useState("");
  const [broker, setBroker] = useState<Broker>("robinhood");
  const [taxTreatment, setTaxTreatment] = useState("");

  const isEdit = !!account;

  useEffect(() => {
    if (account) {
      setName(account.name);
      setBroker(account.broker as Broker);
      setTaxTreatment(account.tax_treatment ?? "");
    } else {
      setName("");
      setBroker("robinhood");
      setTaxTreatment("");
    }
  }, [account, open]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({
      name,
      broker,
      tax_treatment: taxTreatment || undefined,
    });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Account" : "Add Account"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="account-name">Name</Label>
            <Input
              id="account-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Roth IRA"
              required
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="account-broker">Broker</Label>
            <Select value={broker} onValueChange={(v) => setBroker(v as Broker)}>
              <SelectTrigger id="account-broker">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="robinhood">Robinhood</SelectItem>
                <SelectItem value="merrill">Merrill</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="account-tax">Tax Treatment (optional)</Label>
            <Input
              id="account-tax"
              value={taxTreatment}
              onChange={(e) => setTaxTreatment(e.target.value)}
              placeholder="e.g., Roth, Traditional, Taxable"
            />
          </div>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Saving..." : isEdit ? "Save Changes" : "Add Account"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
