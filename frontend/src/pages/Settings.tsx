import { useState } from "react";
import type { Account, Broker } from "@/types/account";
import { useAccounts, useCreateAccount, useUpdateAccount } from "@/hooks/useAccounts";
import { Button } from "@/components/ui/button";
import AccountFormDialog from "@/components/AccountFormDialog";

export default function Settings() {
  const { data: accounts, isLoading, error } = useAccounts();
  const createMutation = useCreateAccount();
  const updateMutation = useUpdateAccount();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);

  function handleAdd() {
    setEditingAccount(null);
    setDialogOpen(true);
  }

  function handleEdit(account: Account) {
    setEditingAccount(account);
    setDialogOpen(true);
  }

  function handleSubmit(data: { name: string; broker: Broker; tax_treatment?: string }) {
    if (editingAccount) {
      updateMutation.mutate(
        { id: editingAccount.id, body: data },
        { onSuccess: () => setDialogOpen(false) }
      );
    } else {
      createMutation.mutate(data, {
        onSuccess: () => setDialogOpen(false),
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
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-2 text-left font-medium">Name</th>
                  <th className="px-4 py-2 text-left font-medium">Broker</th>
                  <th className="px-4 py-2 text-left font-medium">Tax Treatment</th>
                  <th className="px-4 py-2 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((account) => (
                  <tr key={account.id} className="border-b last:border-0">
                    <td className="px-4 py-2">{account.name}</td>
                    <td className="px-4 py-2 capitalize">{account.broker}</td>
                    <td className="px-4 py-2">{account.tax_treatment ?? "—"}</td>
                    <td className="px-4 py-2 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(account)}
                      >
                        Edit
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <AccountFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        account={editingAccount}
        onSubmit={handleSubmit}
        submitting={createMutation.isPending || updateMutation.isPending}
      />
    </div>
  );
}
