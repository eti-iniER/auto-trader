import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

interface LogsParams {
  offset?: number;
  limit?: number;
  from_date?: Date;
  to_date?: Date;
  type?: LogType;
}

const getLogs = async (params: LogsParams = {}) => {
  const searchParams = new URLSearchParams();

  if (params.offset !== undefined) {
    searchParams.append("offset", params.offset.toString());
  }
  if (params.limit) {
    searchParams.append("limit", params.limit.toString());
  }
  if (params.from_date) {
    searchParams.append("from_date", params.from_date.toISOString());
  }
  if (params.to_date) {
    searchParams.append("to_date", params.to_date.toISOString());
  }
  if (params.type) {
    searchParams.append("type", params.type);
  }

  const response = await api.get<PaginatedResponse<Log>>("logs", {
    searchParams: searchParams,
  });
  return response.json();
};

export const useLogs = (params: LogsParams = {}) => {
  return useQuery({
    queryKey: ["logs", params],
    queryFn: () => getLogs(params),
    refetchInterval: 1000 * 30,
    placeholderData: (previousData) => {
      if (previousData) {
        return {
          count: previousData.count,
          next: previousData.next,
          previous: previousData.previous,
          results: [],
        };
      }
      return undefined;
    },
  });
};
