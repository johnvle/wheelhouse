import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Account, AccountCreate, AccountUpdate } from "@/types/account";
import { useAuth } from "@/hooks/useAuth";
import { getAccounts, createAccount, updateAccount } from "@/lib/api";

export function useAccounts() {
  const { session } = useAuth();
  const token = session?.access_token ?? null;

  return useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: () => getAccounts(token),
    enabled: !!token,
  });
}

export function useCreateAccount() {
  const { session } = useAuth();
  const token = session?.access_token ?? null;
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: AccountCreate) => createAccount(body, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
  });
}

export function useUpdateAccount() {
  const { session } = useAuth();
  const token = session?.access_token ?? null;
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: AccountUpdate }) =>
      updateAccount(id, body, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
  });
}
