import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

interface UsersParams {
  offset?: number;
  limit?: number;
}

const getUsers = async (params: UsersParams = {}) => {
  const searchParams = new URLSearchParams();

  if (params.offset !== undefined) {
    searchParams.append("offset", params.offset.toString());
  }
  if (params.limit) {
    searchParams.append("limit", params.limit.toString());
  }

  const response = await api.get<PaginatedResponse<UserAdminDetails>>("users", {
    searchParams: searchParams,
  });
  return response.json();
};

export const useUsers = (params: UsersParams = {}, enabled: boolean = true) => {
  return useQuery({
    queryKey: ["users", params],
    queryFn: () => getUsers(params),
    enabled,
    placeholderData: (previousData) => {
      if (previousData) {
        return {
          count: previousData.count,
          next: previousData.next,
          previous: previousData.previous,
          results: [], // Empty data array to show loading state
        };
      }
      return undefined;
    },
  });
};
