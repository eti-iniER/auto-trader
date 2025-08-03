import { useFetchDividendDates } from "@/api/hooks/instruments/use-fetch-dividend-dates";
import { useInstruments } from "@/api/hooks/instruments/use-instruments";
import { useUploadInstrumentsCsv } from "@/api/hooks/instruments/use-upload-instruments-as-csv";
import { InstrumentsTable } from "@/components/instruments-table";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { FiClock, FiUpload } from "react-icons/fi";
import { toast } from "sonner";
import { z } from "zod";

const uploadSchema = z.object({
  file: z
    .instanceof(FileList)
    .refine((files) => files.length > 0, "Please select a file")
    .refine(
      (files) => files[0]?.name.toLowerCase().endsWith(".csv"),
      "Please select a CSV file",
    ),
});

type UploadFormData = z.infer<typeof uploadSchema>;

export const Instruments = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const offset = (page - 1) * pageSize;

  const {
    data: instrumentsResponse,
    isPending,
    isError,
    error,
  } = useInstruments({
    offset,
    limit: pageSize,
  });

  const uploadMutation = useUploadInstrumentsCsv();
  const fetchDividendDates = useFetchDividendDates();

  const form = useForm<UploadFormData>({
    resolver: zodResolver(uploadSchema),
    disabled: uploadMutation.isPending,
  });

  const instruments = instrumentsResponse?.data || [];
  const totalCount = instrumentsResponse?.count || 0;

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1);
  };

  const onSubmit = (data: UploadFormData) => {
    const file = data.file[0];

    uploadMutation.mutate(file, {
      onSuccess: (response) => {
        toast.success(response.message);
        form.reset();
        // Clear the file input manually
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      },
      onError: (error) => {
        toast.error(`Upload failed: ${error.message}`);
      },
    });
  };

  const handleFetchDividendDates = () => {
    fetchDividendDates.mutate(undefined, {
      onSuccess: () => {
        toast.success("Dividend dates updated!");
      },
      onError: (error) => {
        toast.error(`Failed to fetch dividend dates: ${error.message}`);
      },
    });
  };

  if (isError) {
    return (
      <div className="min-w-0 flex-1 space-y-8 p-8">
        <PageHeader
          title="Instruments"
          description="View and edit your trading instruments and ticker data"
        />
        <div className="flex h-64 items-center justify-center">
          <div className="text-center">
            <p className="mb-2 text-red-600">Error loading instruments</p>
            <p className="text-sm text-gray-500">
              {error?.message || "Something went wrong"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col space-y-8 p-8">
      <PageHeader
        title="Instruments"
        description="View and edit your trading instruments and ticker data"
      />

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <InstrumentsTable
          data={instruments}
          loading={isPending}
          pagination={{
            page,
            pageSize,
            totalCount,
            onPageChange: handlePageChange,
            onPageSizeChange: handlePageSizeChange,
          }}
          additionalInputs={
            <>
              <Form {...form}>
                <form
                  onSubmit={form.handleSubmit(onSubmit)}
                  className="flex items-end gap-3"
                >
                  <FormField
                    control={form.control}
                    name="file"
                    render={({ field: { onChange, ref, ...field } }) => (
                      <FormItem className="min-w-0 flex-1">
                        <FormControl>
                          <Input
                            ref={(e) => {
                              ref(e);
                              fileInputRef.current = e;
                            }}
                            type="file"
                            accept=".csv"
                            onChange={(e) => onChange(e.target.files)}
                            {...field}
                            value={undefined}
                            className="file:bg-muted file:text-muted-foreground hover:file:bg-muted/80 file:mr-3 file:rounded-md file:border-0 file:px-3 file:py-1 file:text-sm file:font-medium"
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                  <Button
                    type="submit"
                    className="flex shrink-0 gap-2"
                    disabled={uploadMutation.isPending}
                  >
                    <FiUpload />
                    {uploadMutation.isPending ? "Uploading..." : "Upload"}
                  </Button>
                </form>
              </Form>
              <Button
                onClick={handleFetchDividendDates}
                disabled={fetchDividendDates.isPending}
                className="flex items-center gap-2"
              >
                {fetchDividendDates.isPending ? (
                  <>
                    <div className="h-4 w-4 animate-spin rounded-full border-b-2 border-current" />
                    Fetching...
                  </>
                ) : (
                  <>
                    <FiClock />
                    Fetch Dividend Dates
                  </>
                )}
              </Button>
            </>
          }
        />
      </div>
    </div>
  );
};
