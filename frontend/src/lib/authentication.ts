import { api } from "@/api/config";

export const refreshToken = async () => {
  const response = await api.post("auth/token");
  return response.json();
};
