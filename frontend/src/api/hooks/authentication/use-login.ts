import { api } from "@/api/config";
import { useMutation } from "@tanstack/react-query";

interface LoginRequest {
  username: string;
  password: string;
}

const login = async (data: LoginRequest) => {
  const response = await api.post("login", {
    json: data,
  });
  return response.json();
};

export const useLogin = () => {
  return useMutation({
    mutationFn: login,
  });
};
