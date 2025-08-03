import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

interface OrdersParams {
  offset?: number;
  limit?: number;
}

const getOrders = async (params: OrdersParams = {}) => {
  const searchParams = new URLSearchParams();

  if (params.offset !== undefined) {
    searchParams.append("offset", params.offset.toString());
  }
  if (params.limit) {
    searchParams.append("limit", params.limit.toString());
  }

  const response = await api.get<PaginatedResponse<Order>>("orders", {
    searchParams: searchParams,
  });
  return response.json();
};

export const useOrders = (params: OrdersParams = {}) => {
  return useQuery({
    queryKey: ["orders", params],
    queryFn: () => getOrders(params),
    refetchInterval: 1000 * 30,
    placeholderData: (previousData) => {
      // Only preserve metadata, not the actual data
      if (previousData) {
        return {
          count: previousData.count,
          next: previousData.next,
          previous: previousData.previous,
          data: [], // Empty data array to show loading state
        };
      }
      return undefined;
    },
  });
};
