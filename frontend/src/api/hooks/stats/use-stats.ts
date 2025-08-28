import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

const getStats = async () => {
  const response = await api.get<UserQuickStatsResponse>("stats");
  return response.json();
};

export const useStats = (enabled: boolean = true) => {
  return useQuery({
    queryKey: ["stats"],
    enabled,
    queryFn: getStats,
    refetchInterval: 1000 * 30,
  });
};
