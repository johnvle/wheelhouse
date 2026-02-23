import { useState } from "react";
import type { Account, Broker } from "@/types/account";
import { useAccounts, useCreateAccount, useUpdateAccount } from "@/hooks/useAccounts";
import { useSettings } from "@/contexts/SettingsContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import AccountFormDialog from "@/components/AccountFormDialog";

export default function Settings() {
  const { data: accounts, isLoading, error } = useAccounts();
  const createMutation = useCreateAccount();
  const updateMutation = useUpdateAccount();
  const { settings, updateSettings } = useSettings();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);

  function handleAdd() {
    setEditingAccount(null);
    setMutationError(null);
    setDialogOpen(true);
  }

  function handleEdit(account: Account) {
    setEditingAccount(account);
    setMutationError(null);
    setDialogOpen(true);
  }

  function handleSubmit(data: { name: string; broker: Broker; tax_treatment?: string }) {
    setMutationError(null);
    if (editingAccount) {
      updateMutation.mutate(
        { id: editingAccount.id, body: data },
        {
          onSuccess: () => setDialogOpen(false),
          onError: (err) => setMutationError(err.message),
        }
      );
    } else {
      createMutation.mutate(data, {
        onSuccess: () => setDialogOpen(false),
        onError: (err) => setMutationError(err.message),
      });
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Settings</h1>
      <p className="text-muted-foreground mt-1">Configure your preferences</p>

      <section className="mt-8">
        <h2 className="text-lg font-semibold">Alert Thresholds</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Configure when alerts trigger on the Open Positions page. Changes take effect immediately.
        </p>

        <div className="mt-4 grid gap-6 sm:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="expirationWarningDays">Expiration warning (days)</Label>
            <Input
              id="expirationWarningDays"
              type="number"
              min={1}
              max={90}
              value={settings.expirationWarningDays}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                if (!isNaN(val) && val >= 1) {
                  updateSettings({ expirationWarningDays: val });
                }
              }}
            />
            <p className="text-xs text-muted-foreground">
              Alert when a position expires within this many days
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="nearStrikeThreshold">Price near strike (%)</Label>
            <Input
              id="nearStrikeThreshold"
              type="number"
              min={1}
              max={50}
              step={1}
              value={Math.round(settings.nearStrikeThreshold * 100)}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                if (!isNaN(val) && val >= 1 && val <= 50) {
                  updateSettings({ nearStrikeThreshold: val / 100 });
                }
              }}
            />
            <p className="text-xs text-muted-foreground">
              Alert when price is within this % of the strike
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="stalePriceMinutes">Stale price (minutes)</Label>
            <Input
              id="stalePriceMinutes"
              type="number"
              min={1}
              max={60}
              value={settings.stalePriceMinutes}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                if (!isNaN(val) && val >= 1) {
                  updateSettings({ stalePriceMinutes: val });
                }
              }}
            />
            <p className="text-xs text-muted-foreground">
              Alert when price data is older than this many minutes
            </p>
          </div>
        </div>
      </section>

      <section className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Accounts</h2>
          <Button size="sm" onClick={handleAdd}>Add Account</Button>
        </div>

        {isLoading && <p className="mt-4 text-muted-foreground">Loading accounts...</p>}
        {error && <p className="mt-4 text-sm text-destructive">Failed to load accounts</p>}

        {accounts && accounts.length === 0 && (
          <p className="mt-4 text-muted-foreground">No accounts yet. Add your first account to get started.</p>
        )}

        {accounts && accounts.length > 0 && (
          <div className="mt-4 rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Broker</TableHead>
                  <TableHead>Tax Treatment</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {accounts.map((account) => (
                  <TableRow key={account.id}>
                    <TableCell>{account.name}</TableCell>
                    <TableCell className="capitalize">{account.broker}</TableCell>
                    <TableCell>{account.tax_treatment ?? "—"}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(account)}
                      >
                        Edit
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </section>

      <AccountFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        account={editingAccount}
        onSubmit={handleSubmit}
        submitting={createMutation.isPending || updateMutation.isPending}
        error={mutationError}
      />
    </div>
  );
}
