import { useDeletePosition } from "@/api/hooks/positions/use-delete-position";
import { usePositions } from "@/api/hooks/positions/use-positions";
import { PageHeader } from "@/components/page-header";
import { PositionsTable } from "@/components/positions-table";
import { useDashboard } from "@/hooks/contexts/use-dashboard";
import { useModal } from "@/hooks/use-modal";
import { usePagination } from "@/hooks/use-pagination";
import { useUserIGSettingsStatus } from "@/hooks/use-user-ig-settings-status";
import { useState } from "react";
import { MdErrorOutline } from "react-icons/md";
import { toast } from "sonner";
import { DeletePositionDialog } from ".";

export const Positions = () => {
  const { settings } = useDashboard();
  const pagination = usePagination({ initialPageSize: 20 });

  const deletePosition = useDeletePosition();
  const deleteDialog = useModal();
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(
    null,
  );

  const status = useUserIGSettingsStatus(settings);

  const {
    data: positionsResponse,
    isPending,
    isError,
    error,
  } = usePositions(
    {
      offset: pagination.offset,
      limit: pagination.pageSize,
    },
    status === "complete",
  );

  const positions = positionsResponse?.results || [];
  const totalCount = positionsResponse?.count || 0;

  const handleDeletePosition = (position: Position) => {
    setSelectedPosition(position);
    deleteDialog.openModal();
  };

  const handleConfirmDelete = () => {
    if (selectedPosition) {
      deletePosition.mutate(selectedPosition.dealId, {
        onSuccess: () => {
          toast.success("Position closed successfully");
        },
        onError: (error) => {
          toast.error("Couldn't close position", {
            description: error.message || "An unknown error occurred",
          });
        },
        onSettled: () => {
          deleteDialog.closeModal();
          setSelectedPosition(null);
        },
      });
    }
  };

  if (status === "incomplete") {
    return (
      <div className="flex-1 p-4 sm:p-8">
        <PageHeader title="Positions" description="View your open positions" />
        <div className="flex h-64 items-center justify-center">
          <div className="text-center">
            <MdErrorOutline className="mx-auto mb-4 h-12 w-12 text-yellow-500" />
            <p className="mb-2 font-medium text-yellow-600">
              IG settings incomplete
            </p>
            <p className="text-muted-foreground text-sm">
              Please complete your IG settings to view positions data
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-w-0 flex-1 space-y-8 p-8">
        <PageHeader title="Positions" description="View your open positions" />
        <div className="flex h-64 items-center justify-center">
          <div className="text-center">
            <p className="mb-2 text-red-600">Error loading positions</p>
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
      <PageHeader title="Positions" description="View your open positions" />

      <div className="min-h-0 flex-1">
        <PositionsTable
          data={positions}
          loading={isPending}
          onDeletePosition={handleDeletePosition}
          pagination={{
            ...pagination.paginationProps,
            totalCount,
          }}
        />
      </div>

      {/* Delete Position Dialog */}
      {selectedPosition && (
        <DeletePositionDialog
          isOpen={deleteDialog.isOpen}
          onClose={deleteDialog.closeModal}
          onConfirm={handleConfirmDelete}
          positionIgEpic={selectedPosition.igEpic}
          loading={deletePosition.isPending}
        />
      )}
    </div>
  );
};
