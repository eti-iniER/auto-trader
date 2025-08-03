import { useOrders } from "@/api/hooks/orders/use-orders";
import { OrdersTable } from "@/components/orders-table";
import { PageHeader } from "@/components/page-header";
import { useState } from "react";

export const Orders = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const offset = (page - 1) * pageSize;

  const {
    data: ordersResponse,
    isPending,
    isError,
    error,
  } = useOrders({
    offset,
    limit: pageSize,
  });

  const orders = ordersResponse?.data || [];
  const totalCount = ordersResponse?.count || 0;

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1);
  };

  if (isError) {
    return (
      <div className="min-w-0 flex-1 space-y-8 p-8">
        <PageHeader title="Orders" description="View your open orders" />
        <div className="flex h-64 items-center justify-center">
          <div className="text-center">
            <p className="mb-2 text-red-600">Error loading orders</p>
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
      <PageHeader title="Orders" description="View your open orders" />

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <OrdersTable
          data={orders}
          loading={isPending}
          pagination={{
            page,
            pageSize,
            totalCount,
            onPageChange: handlePageChange,
            onPageSizeChange: handlePageSizeChange,
          }}
        />
      </div>
    </div>
  );
};
