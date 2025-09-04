import { api } from "@/api/config";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const deleteOrder = async (dealId: string) => {
  const response = await api.delete(`orders/${dealId}`);
  return response.json();
};

export const useDeleteOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
};
