import { api } from "@/api/config";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const deleteUser = async (userId: string) => {
  const response = await api.delete<SimpleResponse>(`users/${userId}`);
  return response.json();
};

export const useDeleteUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
};
