import { useDeleteUser } from "@/api/hooks/users/use-delete-user";
import { useUpdateUser } from "@/api/hooks/users/use-update-user";
import { useUsers } from "@/api/hooks/users/use-users";
import { PageHeader } from "@/components/page-header";
import { UsersTable } from "@/components/users-table";
import { useDashboardContext } from "@/hooks/contexts/use-dashboard-context";
import { useModal } from "@/hooks/use-modal";
import { usePagination } from "@/hooks/use-pagination";
import { useState } from "react";
import { Navigate } from "react-router";
import { toast } from "sonner";
import { DeleteUserDialog } from "./delete-user-dialog";
import { EditUserModal } from "./edit-user-modal";

interface EditUserData {
  firstName: string;
  lastName: string;
  email: string;
  role: "USER" | "ADMIN";
}

export const Users: React.FC = () => {
  const { user } = useDashboardContext();
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
  // Modal state management
  const editModal = useModal();
  const deleteDialog = useModal();
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
    </>
  );
};
