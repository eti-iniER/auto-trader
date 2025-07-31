import { api } from "@/api/config";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const uploadInstrumentsCsv = async (
  file: File,
): Promise<InstrumentUploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("instruments/upload-csv", {
    body: formData,
  });

  return response.json();
};

export const useUploadInstrumentsCsv = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: uploadInstrumentsCsv,
    onSuccess: () => {
      // Invalidate instruments queries to refresh the data
      queryClient.invalidateQueries({ queryKey: ["instruments"] });
    },
  });
};
