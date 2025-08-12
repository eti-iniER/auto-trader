import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader } from "@/components/ui/loader";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type ColumnFiltersState,
  type Row,
  type SortingState,
} from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import { ArrowUpDown, ChevronDown, ChevronUp } from "lucide-react";
import * as React from "react";

export interface VirtualizedTableProps<TData, TValue = unknown> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  loading?: boolean;
  searchPlaceholder?: string;
  pagination?: {
    page: number;
    pageSize: number;
    totalCount: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (pageSize: number) => void;
  };
  className?: string;
  rowHeight?: number;
  maxHeight?: number;
  fillAvailableHeight?: boolean;
  additionalInputs?: React.ReactNode;
}

function VirtualizedTable<TData, TValue = unknown>({
  columns,
  data,
  loading = false,
  searchPlaceholder = "Search...",
  pagination,
  className,
  rowHeight = 45,
  maxHeight = 600,
  fillAvailableHeight = false,
  additionalInputs,
}: VirtualizedTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    [],
  );
  const [globalFilter, setGlobalFilter] = React.useState("");

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    onColumnFiltersChange: setColumnFilters,
    getFilteredRowModel: getFilteredRowModel(),
    onGlobalFilterChange: setGlobalFilter,
    globalFilterFn: "includesString",
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
  });

  const { rows } = table.getRowModel();

  const parentRef = React.useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => rowHeight,
    overscan: 10,
  });

  const virtualItems = virtualizer.getVirtualItems();
  const totalSize = virtualizer.getTotalSize();

  const paddingTop = virtualItems.length > 0 ? virtualItems[0]?.start || 0 : 0;
  const paddingBottom =
    virtualItems.length > 0
      ? totalSize - (virtualItems[virtualItems.length - 1]?.end || 0)
      : 0;

  return (
    <div
      className={cn(
        "space-y-4",
        fillAvailableHeight && "flex h-full flex-col",
        className,
      )}
    >
      <div className="flex justify-start gap-2">
        <Input
          placeholder={searchPlaceholder}
          value={globalFilter ?? ""}
          onChange={(event) => setGlobalFilter(event.target.value)}
          className="w-full max-w-sm sm:max-w-sm"
        />
        {additionalInputs}
      </div>

      <div
        className={cn(
          "w-full overflow-hidden rounded-md border",
          fillAvailableHeight && "min-h-0 flex-1",
        )}
      >
        <div
          ref={parentRef}
          className="scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100 relative w-full overflow-auto"
          style={{
            height: fillAvailableHeight ? "100%" : `${maxHeight}px`,
            maxHeight: fillAvailableHeight ? "100%" : `${maxHeight}px`,
            willChange: "scroll-position",
            transform: "translateZ(0)", // Force hardware acceleration
            scrollBehavior: "auto", // Disable smooth scrolling for performance
            WebkitOverflowScrolling: "touch", // Better mobile scrolling
          }}
        >
          <Table className="w-full" style={{ minWidth: "800px" }}>
            <TableHeader className="bg-background sticky top-0 z-10">
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHead key={header.id} className="relative">
                      {header.isPlaceholder ? null : (
                        <div
                          className={cn(
                            "flex items-center space-x-2",
                            header.column.getCanSort() &&
                              "hover:bg-accent/50 -mx-2 -my-1 cursor-pointer rounded px-2 py-1 select-none",
                          )}
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                          {header.column.getCanSort() && (
                            <div className="ml-1 flex flex-col">
                              {header.column.getIsSorted() === "desc" ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : header.column.getIsSorted() === "asc" ? (
                                <ChevronUp className="h-4 w-4" />
                              ) : (
                                <ArrowUpDown className="h-4 w-4 opacity-50" />
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell
                    colSpan={columns.length}
                    className="h-24 text-center"
                  >
                    <div className="flex flex-col items-center justify-center gap-2">
                      <Loader variant="dark" />
                      <span>Loading</span>
                    </div>
                  </TableCell>
                </TableRow>
              ) : virtualItems.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={columns.length}
                    className="h-24 text-center"
                  >
                    No results.
                  </TableCell>
                </TableRow>
              ) : (
                <>
                  {/* Top padding */}
                  {paddingTop > 0 && (
                    <tr>
                      <td style={{ height: `${paddingTop}px` }} />
                    </tr>
                  )}

                  {/* Virtual rows */}
                  {virtualItems.map((virtualRow) => {
                    const row = rows[virtualRow.index] as Row<TData>;
                    return (
                      <TableRow
                        key={row.id}
                        data-state={row.getIsSelected() && "selected"}
                        style={{
                          height: `${virtualRow.size}px`,
                          transform: "translateZ(0)", // Force layer creation for smoother scrolling
                        }}
                      >
                        {row.getVisibleCells().map((cell) => (
                          <TableCell
                            key={cell.id}
                            style={{ willChange: "auto" }}
                          >
                            {flexRender(
                              cell.column.columnDef.cell,
                              cell.getContext(),
                            )}
                          </TableCell>
                        ))}
                      </TableRow>
                    );
                  })}

                  {/* Bottom padding */}
                  {paddingBottom > 0 && (
                    <tr>
                      <td style={{ height: `${paddingBottom}px` }} />
                    </tr>
                  )}
                </>
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Pagination */}
      {pagination && (
        <div
          className={cn(
            "flex flex-col space-y-4 px-2 sm:flex-row sm:items-center sm:justify-between sm:space-y-0",
            fillAvailableHeight && "flex-shrink-0",
          )}
        >
          <div className="text-muted-foreground text-sm">
            Showing{" "}
            {Math.min(
              (pagination.page - 1) * pagination.pageSize + 1,
              pagination.totalCount,
            )}{" "}
            to{" "}
            {Math.min(
              pagination.page * pagination.pageSize,
              pagination.totalCount,
            )}{" "}
            of {pagination.totalCount} entries
          </div>
          <div className="flex flex-col space-y-4 sm:flex-row sm:items-center sm:space-y-0 sm:space-x-6 lg:space-x-8">
            <div className="flex items-center justify-between space-x-2 sm:justify-start">
              <p className="text-sm font-medium">Rows per page</p>
              <Select
                value={pagination.pageSize.toString()}
                onValueChange={(value) =>
                  pagination.onPageSizeChange(Number(value))
                }
              >
                <SelectTrigger className="h-10 w-[80px] sm:h-8 sm:w-[70px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[10, 20, 30, 40, 50].map((pageSize) => (
                    <SelectItem key={pageSize} value={pageSize.toString()}>
                      {pageSize}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center justify-center text-sm font-medium sm:w-[100px]">
              Page {pagination.page} of{" "}
              {Math.ceil(pagination.totalCount / pagination.pageSize)}
            </div>
            <div className="flex items-center justify-center space-x-1 sm:justify-start sm:space-x-2">
              <Button
                variant="outline"
                className="h-10 w-10 p-0 sm:h-8 sm:w-8"
                onClick={() => pagination.onPageChange(1)}
                disabled={pagination.page <= 1}
              >
                <span className="sr-only">Go to first page</span>
                {"<<"}
              </Button>
              <Button
                variant="outline"
                className="h-10 w-10 p-0 sm:h-8 sm:w-8"
                onClick={() => pagination.onPageChange(pagination.page - 1)}
                disabled={pagination.page <= 1}
              >
                <span className="sr-only">Go to previous page</span>
                {"<"}
              </Button>
              <Button
                variant="outline"
                className="h-10 w-10 p-0 sm:h-8 sm:w-8"
                onClick={() => pagination.onPageChange(pagination.page + 1)}
                disabled={
                  pagination.page >=
                  Math.ceil(pagination.totalCount / pagination.pageSize)
                }
              >
                <span className="sr-only">Go to next page</span>
                {">"}
              </Button>
              <Button
                variant="outline"
                className="h-10 w-10 p-0 sm:h-8 sm:w-8"
                onClick={() =>
                  pagination.onPageChange(
                    Math.ceil(pagination.totalCount / pagination.pageSize),
                  )
                }
                disabled={
                  pagination.page >=
                  Math.ceil(pagination.totalCount / pagination.pageSize)
                }
              >
                <span className="sr-only">Go to last page</span>
                {">>"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export { VirtualizedTable };
