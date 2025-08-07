import { api } from "@/api/config";
import { useMutation } from "@tanstack/react-query";

interface ChangePasswordRequest {
  newPassword: string;
}

const changePassword = async (data: ChangePasswordRequest) => {
  const response = await api.patch("users/me/change-password", {
    json: data,
  });
  return response.json();
};

export const useChangePassword = () => {
  return useMutation({
    mutationFn: changePassword,
  });
};
