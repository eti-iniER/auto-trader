import { api } from "@/api/config";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const deletePosition = async (dealId: string) => {
  const response = await api.delete(`positions/${dealId}`);
  return response.json();
};

export const useDeletePosition = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deletePosition,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["positions"] });
    },
  });
};
