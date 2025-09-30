import { useDeleteUser } from "@/api/hooks/users/use-delete-user";
import { useUpdateUser } from "@/api/hooks/users/use-update-user";
import { useUsers } from "@/api/hooks/users/use-users";
import { useDeleteUserLogs } from "@/api/hooks/logs/use-delete-user-logs";
import { useDownloadUserLogs } from "@/api/hooks/logs/use-download-user-logs";
import { PageHeader } from "@/components/page-header";
import { UsersTable } from "@/components/users-table";
import { useDashboard } from "@/hooks/contexts/use-dashboard";
import { useModal } from "@/hooks/use-modal";
import { usePagination } from "@/hooks/use-pagination";
import { useState } from "react";
import { Navigate } from "react-router";
import { toast } from "sonner";
import { DeleteUserDialog } from "./delete-user-dialog";
import { DeleteUserLogsDialog } from "./delete-user-logs-dialog";
import { EditUserModal } from "./edit-user-modal";

interface EditUserData {
  firstName: string;
  lastName: string;
  email: string;
  role: "USER" | "ADMIN";
}

export const Users: React.FC = () => {
  const { user } = useDashboard();
  const pagination = usePagination({ initialPageSize: 20 });

  const {
    data: usersResponse,
    isPending: isUsersLoading,
    isError,
    error,
  } = useUsers({
    offset: pagination.offset,
    limit: pagination.pageSize,
  });

  const users = usersResponse?.results || [];
  const totalCount = usersResponse?.count || 0;

  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();
  const deleteUserLogs = useDeleteUserLogs();
  const downloadUserLogs = useDownloadUserLogs();
  // Modal state management
  const editModal = useModal();
  const deleteDialog = useModal();
  const deleteLogsDialog = useModal();
  const [selectedUser, setSelectedUser] = useState<UserAdminDetails | null>(
    null,
  );

  // Check if user is admin, if not redirect them
  if (user.role !== "ADMIN") {
    return <Navigate to="/dashboard/overview" replace />;
  }

  const handleEditUser = (user: UserAdminDetails) => {
    setSelectedUser(user);
    editModal.openModal();
  };

  const handleDeleteUser = (user: UserAdminDetails) => {
    setSelectedUser(user);
    deleteDialog.openModal();
  };

  const handleDeleteUserLogs = (user: UserAdminDetails) => {
    setSelectedUser(user);
    deleteLogsDialog.openModal();
  };

  const handleDownloadUserLogs = (user: UserAdminDetails) => {
    downloadUserLogs.mutate(user.id, {
      onSuccess: () => {
        toast.success("User logs downloaded successfully");
      },
      onError: (error) => {
        toast.error("Couldn't download user logs", {
          description: error.message || "An unknown error occurred",
        });
      },
    });
  };

  const handleSaveUser = (userData: EditUserData) => {
    if (selectedUser) {
      updateUser.mutate(
        { userId: selectedUser.id, userData },
        {
          onSuccess: () => {
            toast.success("User updated successfully");
          },
          onError: (error) => {
            toast.error("Couldn't update user", {
              description: error.message || "An unknown error occurred",
            });
          },
          onSettled: () => {
            editModal.closeModal();
            setSelectedUser(null);
          },
        },
      );
    }
  };

  const handleConfirmDelete = () => {
    if (selectedUser) {
      deleteUser.mutate(selectedUser.id, {
        onSuccess: () => {
          toast.success("User deleted successfully");
        },
        onError: (error) => {
          toast.error("Couldn't delete user", {
            description: error.message || "An unknown error occurred",
          });
        },
        onSettled: () => {
          deleteDialog.closeModal();
          setSelectedUser(null);
        },
      });
    }
  };

  const handleConfirmDeleteLogs = () => {
    if (selectedUser) {
      deleteUserLogs.mutate(selectedUser.id, {
        onSuccess: () => {
          toast.success("User logs deleted successfully");
        },
        onError: (error) => {
          toast.error("Couldn't delete user logs", {
            description: error.message || "An unknown error occurred",
          });
        },
        onSettled: () => {
          deleteLogsDialog.closeModal();
          setSelectedUser(null);
        },
      });
    }
  };

  if (isError) {
    return (
      <>
        <div className="min-w-0 flex-1 space-y-8 p-8">
          <PageHeader
            title="Users"
            description="Manage user accounts and permissions"
          />
          <div className="flex h-64 items-center justify-center">
            <div className="text-center">
              <p className="mb-2 text-red-600">Error loading users</p>
              <p className="text-sm text-gray-500">
                {error?.message || "Something went wrong"}
              </p>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="flex h-full flex-col space-y-6 p-8">
        <PageHeader
          title="Users"
          description="Manage user accounts and permissions"
        />

        <div className="min-h-0 flex-1">
          <UsersTable
            data={users}
            loading={isUsersLoading}
            className="h-full"
            onEditUser={handleEditUser}
            onDeleteUser={handleDeleteUser}
            onDeleteUserLogs={handleDeleteUserLogs}
            onDownloadUserLogs={handleDownloadUserLogs}
            pagination={{
              ...pagination.paginationProps,
              totalCount,
            }}
          />
        </div>
      </div>

      {/* Edit User Modal */}
      {selectedUser && (
        <EditUserModal
          isOpen={editModal.isOpen}
          onClose={editModal.closeModal}
          onSave={handleSaveUser}
          user={selectedUser}
        />
      )}

      {/* Delete User Dialog */}
      {selectedUser && (
        <DeleteUserDialog
          isOpen={deleteDialog.isOpen}
          onClose={deleteDialog.closeModal}
          onConfirm={handleConfirmDelete}
          userName={`${selectedUser.firstName} ${selectedUser.lastName}`}
        />
      )}

      {/* Delete User Logs Dialog */}
      {selectedUser && (
        <DeleteUserLogsDialog
          isOpen={deleteLogsDialog.isOpen}
          onClose={deleteLogsDialog.closeModal}
          onConfirm={handleConfirmDeleteLogs}
          userName={`${selectedUser.firstName} ${selectedUser.lastName}`}
          loading={deleteUserLogs.isPending}
        />
      )}
    </>
  );
};
