import { api } from "@/api/config";
import { useMutation } from "@tanstack/react-query";

interface LoginRequest {
  email: string;
  password: string;
}

const login = async (data: LoginRequest) => {
  const response = await api.post("auth/login", {
    json: data,
  });
  return response.json();
};

export const useLogin = () => {
  return useMutation({
    mutationFn: login,
  });
};
