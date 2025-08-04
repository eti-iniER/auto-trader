import { api } from "@/api/config";
import { useMutation } from "@tanstack/react-query";

interface ResetPasswordRequest {
  email: string;
}

const resetPassword = async (data: ResetPasswordRequest) => {
  const response = await api.post("auth/reset-password", {
    json: data,
  });
  return response.json();
};

export const useResetPassword = () => {
  return useMutation({
    mutationFn: resetPassword,
  });
};
