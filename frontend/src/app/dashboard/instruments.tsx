import { useFetchDividendDates } from "@/api/hooks/instruments/use-fetch-dividend-dates";
import { useInstruments } from "@/api/hooks/instruments/use-instruments";
import { useSearchInstruments } from "@/api/hooks/instruments/use-search-instruments";
import { useUploadInstrumentsCsv } from "@/api/hooks/instruments/use-upload-instruments-as-csv";
import { InstrumentsTable } from "@/components/instruments-table";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Loader } from "@/components/ui/loader";
import { useDebounce } from "@/hooks/use-debounce";
import { usePagination } from "@/hooks/use-pagination";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { FiClock, FiUpload } from "react-icons/fi";
import { useSearchParams } from "react-router";
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
  const pagination = usePagination({ initialPageSize: 20 });
  const [searchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || "");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Debounce the search query to prevent excessive API calls
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  const hasSearchQuery = !!debouncedSearchQuery.trim();

  // Use search API when there's a search query, otherwise use regular instruments API
  const {
    data: instrumentsResponse,
    isPending,
    isError,
    error,
  } = useInstruments({
    offset: pagination.offset,
    limit: pagination.pageSize,
  });

  const {
    data: searchResponse,
    isPending: isSearchPending,
    isError: isSearchError,
    error: searchError,
  } = useSearchInstruments(
    {
      q: debouncedSearchQuery,
      offset: pagination.offset,
      limit: pagination.pageSize,
    },
    hasSearchQuery,
  );

  // Use search results when searching, otherwise use regular instruments
  const currentResponse = hasSearchQuery ? searchResponse : instrumentsResponse;
  const currentIsPending = hasSearchQuery ? isSearchPending : isPending;
  const currentIsError = hasSearchQuery ? isSearchError : isError;
  const currentError = hasSearchQuery ? searchError : error;

  const uploadMutation = useUploadInstrumentsCsv();
  const fetchDividendDates = useFetchDividendDates();

  const form = useForm<UploadFormData>({
    resolver: zodResolver(uploadSchema),
    disabled: uploadMutation.isPending,
  });

  const instruments = currentResponse?.results || [];
  const totalCount = currentResponse?.count || 0;

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    pagination.setPage(1); // Reset to first page when searching
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
        toast.success("Success!", {
          description:
            "Dividend dates are being fetched in the background. Please check back in a few minutes.",
        });
      },
      onError: (error) => {
        toast.error(`Failed to fetch dividend dates: ${error.message}`);
      },
    });
  };

  if (currentIsError) {
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
              {currentError?.message || "Something went wrong"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col space-y-8 p-8">
      <PageHeader
        title="Instruments"
        description="View and edit your trading instruments and ticker data"
      />

      <div className="f min-h-0 flex-1">
        <InstrumentsTable
          data={instruments}
          loading={currentIsPending}
          pagination={{
            ...pagination.paginationProps,
            totalCount,
          }}
          searchValue={searchQuery}
          onSearchChange={handleSearchChange}
          additionalInputs={
            <div className="flex w-full flex-col gap-2 md:flex-row md:gap-3">
              <Form {...form}>
                <form
                  onSubmit={form.handleSubmit(onSubmit)}
                  className="flex flex-col gap-2 md:flex-row md:items-end md:gap-3"
                >
                  <FormField
                    control={form.control}
                    name="file"
                    render={({ field: { onChange, ref, ...field } }) => (
                      <FormItem className="w-full md:min-w-0 md:flex-1">
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
                    className="flex w-full shrink-0 gap-2 md:w-auto"
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
                className="flex w-full items-center gap-2 md:w-auto"
              >
                {fetchDividendDates.isPending ? (
                  <>
                    <Loader variant="light" />
                    Fetching...
                  </>
                ) : (
                  <>
                    <FiClock />
                    Fetch dividend dates
                  </>
                )}
              </Button>
            </div>
          }
        />
      </div>
    </div>
  );
};
