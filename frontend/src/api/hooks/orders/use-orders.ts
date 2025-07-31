import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

interface OrdersParams {
  page?: number;
  pageSize?: number;
  search?: string;
}

const getOrders = async (params: OrdersParams = {}) => {
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

  const response = await api.get("orders", {
    searchParams: searchParams,
  });
  return response.json();
};

export const useOrders = (params: OrdersParams = {}) => {
  return useQuery({
    queryKey: ["orders", params],
    queryFn: () => getOrders(params),
    refetchInterval: 1000 * 30,
  });
};
