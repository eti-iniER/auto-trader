import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

interface InstrumentsParams {
  offset?: number;
  limit?: number;
}

const getInstruments = async (params: InstrumentsParams = {}) => {
  const searchParams = new URLSearchParams();

  if (params.offset !== undefined) {
    searchParams.append("offset", params.offset.toString());
  }
  if (params.limit) {
    searchParams.append("limit", params.limit.toString());
  }

  const response = await api.get<PaginatedResponse<Instrument>>("instruments", {
    searchParams: searchParams,
  });
  return response.json();
};

export const useInstruments = (params: InstrumentsParams = {}) => {
  return useQuery({
    queryKey: ["instruments", params],
    queryFn: () => getInstruments(params),
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
