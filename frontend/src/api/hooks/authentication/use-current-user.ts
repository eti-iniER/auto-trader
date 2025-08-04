import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

const getCurrentUser = async () => {
  const response = await api.get<User>("auth/me");
  return response.json();
};

export const useCurrentUser = () => {
  return useQuery({
    queryKey: ["me"],
    queryFn: getCurrentUser,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 2,
  });
};
