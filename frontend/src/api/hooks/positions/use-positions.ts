import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

interface PositionsParams {
  offset?: number;
  limit?: number;
}

const getPositions = async (params: PositionsParams = {}) => {
  const searchParams = new URLSearchParams();

  if (params.offset !== undefined) {
    searchParams.append("offset", params.offset.toString());
  }
  if (params.limit) {
    searchParams.append("limit", params.limit.toString());
  }

  const response = await api.get<PaginatedResponse<Position>>("positions", {
    searchParams: searchParams,
  });
  return response.json();
};

export const usePositions = (params: PositionsParams = {}) => {
  return useQuery({
    queryKey: ["positions", params],
    queryFn: () => getPositions(params),
    refetchInterval: 1000 * 10, // Refetch every 10 seconds
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
