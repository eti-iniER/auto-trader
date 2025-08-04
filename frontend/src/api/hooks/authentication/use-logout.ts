import { api } from "@/api/config";
import { useMutation } from "@tanstack/react-query";

const logout = async () => {
  const response = await api.post("auth/logout");
  return response.json();
};

export const useLogout = () => {
  return useMutation({
    mutationFn: logout,
  });
};
