import { api } from "@/api/config";
import { useMutation } from "@tanstack/react-query";

interface DownloadLogsParams {
  fromDate?: Date;
  toDate?: Date;
  type?: LogType;
}

const downloadLogs = async (params: DownloadLogsParams = {}) => {
  const searchParams = new URLSearchParams();

  if (params.fromDate) {
    searchParams.append("from_date", params.fromDate.toISOString());
  }
  if (params.toDate) {
    searchParams.append("to_date", params.toDate.toISOString());
  }
  if (params.type) {
    searchParams.append("type", params.type);
  }

  const response = await api.get("logs/download", {
    searchParams: searchParams,
  });

  const contentDisposition = response.headers.get("content-disposition");
  const timestamp = new Date()
    .toISOString()
    .replace(/T/, " at ")
    .replace(/:/g, "-")
    .replace(/\..+/, "");
  let filename = `logs_${timestamp}.log`;

  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
    if (filenameMatch) {
      filename = filenameMatch[1];
    }
  }

  const blob = await response.blob();

  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();

  // Cleanup
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);

  return { filename, size: blob.size };
};

export const useDownloadLogs = () => {
  return useMutation({
    mutationFn: downloadLogs,
  });
};
