import { useDeleteOrder } from "@/api/hooks/orders/use-delete-order";
import { useOrders } from "@/api/hooks/orders/use-orders";
import { OrdersTable } from "@/components/orders-table";
import { PageHeader } from "@/components/page-header";
import { useDashboardContext } from "@/hooks/contexts/use-dashboard-context";
import { useModal } from "@/hooks/use-modal";
import { usePagination } from "@/hooks/use-pagination";
import { useUserIGSettingsStatus } from "@/hooks/use-user-ig-settings-status";
import { useState } from "react";
import { MdErrorOutline } from "react-icons/md";
import { toast } from "sonner";
import { DeleteOrderDialog } from ".";

export const Orders = () => {
  const { settings } = useDashboardContext();
  const pagination = usePagination({ initialPageSize: 20 });
  const status = useUserIGSettingsStatus(settings);

  const deleteOrder = useDeleteOrder();
  const deleteDialog = useModal();
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  const {
    data: ordersResponse,
    isPending,
    isError,
    error,
  } = useOrders(
    {
      offset: pagination.offset,
      limit: pagination.pageSize,
    },
    status === "complete",
  );

  const orders = ordersResponse?.results || [];
  const totalCount = ordersResponse?.count || 0;

  const handleDeleteOrder = (order: Order) => {
    setSelectedOrder(order);
    deleteDialog.openModal();
  };

  const handleConfirmDelete = () => {
    if (selectedOrder) {
      deleteOrder.mutate(selectedOrder.dealId, {
        onSuccess: () => {
          toast.success("Order deleted successfully");
        },
        onError: (error) => {
          toast.error("Couldn't delete order", {
            description: error.message || "An unknown error occurred",
          });
        },
        onSettled: () => {
          deleteDialog.closeModal();
          setSelectedOrder(null);
        },
      });
    }
  };

  if (status === "incomplete") {
    return (
      <div className="flex-1 p-4 sm:p-8">
        <PageHeader title="Orders" description="View your open orders" />
        <div className="flex h-64 items-center justify-center">
          <div className="text-center">
            <MdErrorOutline className="mx-auto mb-4 h-12 w-12 text-yellow-500" />
            <p className="mb-2 font-medium text-yellow-600">
              IG settings incomplete
            </p>
            <p className="text-muted-foreground text-sm">
              Please complete your IG settings to view orders data
            </p>
          </div>
        </div>
      </div>
    );
  }

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
    <div className="flex h-full flex-col space-y-8 p-8">
      <PageHeader title="Orders" description="View your open orders" />

      <div className="min-h-0 flex-1">
        <OrdersTable
          data={orders}
          loading={isPending}
          onDeleteOrder={handleDeleteOrder}
          pagination={{
            ...pagination.paginationProps,
            totalCount,
          }}
        />
      </div>

      {/* Delete Order Dialog */}
      {selectedOrder && (
        <DeleteOrderDialog
          isOpen={deleteDialog.isOpen}
          onClose={deleteDialog.closeModal}
          onConfirm={handleConfirmDelete}
          orderIgEpic={selectedOrder.igEpic}
          loading={deleteOrder.isPending}
        />
      )}
    </div>
  );
};
