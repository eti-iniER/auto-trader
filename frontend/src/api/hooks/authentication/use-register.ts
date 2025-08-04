import { api } from "@/api/config";
import { useMutation } from "@tanstack/react-query";

interface RegisterRequest {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
}

const register = async (data: RegisterRequest) => {
  const response = await api.post("auth/register", {
    json: data,
  });
  return response.json();
};

export const useRegister = () => {
  return useMutation({
    mutationFn: register,
  });
};
