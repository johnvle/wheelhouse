import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import { createPosition, type PositionCreateBody } from "@/lib/api";

export function useCreatePosition() {
  const { session } = useAuth();
  const token = session?.access_token ?? null;
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: PositionCreateBody) => createPosition(body, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["positions"] });
    },
  });
}
