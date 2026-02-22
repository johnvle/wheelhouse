import { useState } from "react";
import type { Account, Broker } from "@/types/account";
import { useAccounts, useCreateAccount, useUpdateAccount } from "@/hooks/useAccounts";
import { Button } from "@/components/ui/button";
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
