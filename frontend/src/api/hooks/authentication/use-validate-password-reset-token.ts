import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

interface ValidatePasswordResetTokenRequest {
  token: string;
}

const validatePasswordResetToken = async (
  data: ValidatePasswordResetTokenRequest,
) => {
  const response = await api.post("auth/validate-password-reset-token", {
    json: data,
  });
  return response.json();
};

export const useValidatePasswordResetToken = (
  token: string,
  enabled: boolean = true,
) => {
  return useQuery({
    queryKey: ["validate-password-reset-token", token],
    queryFn: () => validatePasswordResetToken({ token }),
    enabled: enabled && !!token,
    retry: false,
  });
};
