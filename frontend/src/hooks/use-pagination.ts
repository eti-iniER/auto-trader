import { useState, useMemo } from "react";

export interface PaginationState {
  page: number;
  pageSize: number;
  offset: number;
}

export interface PaginationActions {
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  handlePageChange: (newPage: number) => void;
  handlePageSizeChange: (newPageSize: number) => void;
  reset: () => void;
}

export interface UsePaginationOptions {
  initialPage?: number;
  initialPageSize?: number;
}

export interface UsePaginationReturn
  extends PaginationState,
    PaginationActions {
  paginationProps: {
    page: number;
    pageSize: number;
    onPageChange: (newPage: number) => void;
    onPageSizeChange: (newPageSize: number) => void;
  };
}

/**
 * Custom hook to manage pagination state
 * @param options - Configuration options for pagination
 * @returns Pagination state and actions
 */
export const usePagination = (
  options: UsePaginationOptions = {},
): UsePaginationReturn => {
  const { initialPage = 1, initialPageSize = 20 } = options;

  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);

  // Calculate offset based on current page and pageSize
  const offset = useMemo(() => (page - 1) * pageSize, [page, pageSize]);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1); // Reset to first page when page size changes
  };

  const reset = () => {
    setPage(initialPage);
    setPageSize(initialPageSize);
  };

  // Pre-configured props object for easy spreading into table components
  const paginationProps = useMemo(
    () => ({
      page,
      pageSize,
      onPageChange: handlePageChange,
      onPageSizeChange: handlePageSizeChange,
    }),
    [page, pageSize],
  );

  return {
    page,
    pageSize,
    offset,
    setPage,
    setPageSize,
    handlePageChange,
    handlePageSizeChange,
    reset,
    paginationProps,
  };
};
