import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

const getUsers = async () => {
  const response = await api.get<PaginatedResponse<UserAdminDetails>>("users/");
  return response.json();
};

export const useUsers = () => {
  return useQuery({
    queryKey: ["users"],
    queryFn: getUsers,
    staleTime: 1000 * 60 * 5,
    retry: 2,
  });
};
