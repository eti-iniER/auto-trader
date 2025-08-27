import { api } from "@/api/config";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const updateUser = async (
  userId: string,
  userData: Partial<UserAdminDetails>,
) => {
  const response = await api.patch<SimpleResponse>(`users/${userId}`, {
    json: userData,
  });
  return response.json();
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      userId,
      userData,
    }: {
      userId: string;
      userData: Partial<UserAdminDetails>;
    }) => updateUser(userId, userData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
};
