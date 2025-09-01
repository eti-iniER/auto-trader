import { api } from "@/api/config";
import { useQuery } from "@tanstack/react-query";

interface SearchInstrumentsParams {
  q?: string; // Universal search query
  marketAndSymbol?: string;
  igEpic?: string;
  yahooSymbol?: string;
  offset?: number;
  limit?: number;
}

const searchInstruments = async (params: SearchInstrumentsParams = {}) => {
  const searchParams = new URLSearchParams();

  if (params.q) {
    searchParams.append("q", params.q);
  }
  if (params.marketAndSymbol) {
    searchParams.append("market_and_symbol", params.marketAndSymbol);
  }
  if (params.igEpic) {
    searchParams.append("ig_epic", params.igEpic);
  }
  if (params.yahooSymbol) {
    searchParams.append("yahoo_symbol", params.yahooSymbol);
  }
  if (params.offset !== undefined) {
    searchParams.append("offset", params.offset.toString());
  }
  if (params.limit) {
    searchParams.append("limit", params.limit.toString());
  }

  const response = await api.get<PaginatedResponse<Instrument>>(
    "instruments/search",
    {
      searchParams: searchParams,
    },
  );
  return response.json();
};

export const useSearchInstruments = (
  params: SearchInstrumentsParams = {},
  enabled: boolean = true,
) => {
  return useQuery({
    queryKey: ["instruments", "search", params],
    queryFn: () => searchInstruments(params),
    enabled:
      enabled &&
      (!!params.q ||
        !!params.marketAndSymbol ||
        !!params.igEpic ||
        !!params.yahooSymbol),
    staleTime: 1000 * 60 * 2, // 2 minutes
    retry: 2,
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
