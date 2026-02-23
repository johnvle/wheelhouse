import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import { closePosition, type PositionCloseBody } from "@/lib/api";

export function useClosePosition() {
  const { session } = useAuth();
  const token = session?.access_token ?? null;
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: PositionCloseBody }) =>
      closePosition(id, body, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["positions"] });
    },
  });
}
