import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

export interface PaginatedOrdersResponse {
  count: number;
  next: string | null;
  previous: string | null;
  data: Order[];
}

interface OrdersParams {
  page?: number;
  pageSize?: number;
  search?: string;
}

const fetchOrders = async (
  params: OrdersParams = {},
): Promise<PaginatedOrdersResponse> => {
  const searchParams = new URLSearchParams();

  if (params.page) {
    searchParams.append("page", params.page.toString());
  }
  if (params.pageSize) {
    searchParams.append("page_size", params.pageSize.toString());
  }
  if (params.search) {
    searchParams.append("search", params.search);
  }

  const response = await api.get(`orders?${searchParams.toString()}`);
  return response.json();
};

export const useOrders = (params: OrdersParams = {}) => {
  return useQuery({
    queryKey: ["orders", params],
    queryFn: () => fetchOrders(params),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};
