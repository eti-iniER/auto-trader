import { api } from "@/api/config";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const fetchDividendDates = async (): Promise<DividendFetchResponse> => {
  const response = await api.post("instruments/fetch-dividend-dates");
  return response.json();
};

const fetchSingleDividendDate = async (
  instrumentId: string,
): Promise<DividendFetchResponse> => {
  const response = await api.post(
    `instruments/${instrumentId}/fetch-dividend-date`,
  );
  return response.json();
};

export const useFetchDividendDates = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: fetchDividendDates,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["instruments"] });
    },
  });
};

export const useFetchSingleDividendDate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: fetchSingleDividendDate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["instruments"] });
    },
  });
};
