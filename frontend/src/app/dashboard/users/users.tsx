import { useDeleteUser } from "@/api/hooks/users/use-delete-user";
import { useUpdateUser } from "@/api/hooks/users/use-update-user";
import { useUsers } from "@/api/hooks/users/use-users";
import { PageHeader } from "@/components/page-header";
import { UsersTable } from "@/components/users-table";
import { useDashboardContext } from "@/hooks/contexts/use-dashboard-context";
import { useModal } from "@/hooks/use-modal";
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
  const { data: usersData, isPending: isUsersLoading } = useUsers();
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
            editModal.closeModal();
          },
          onError: (error) => {
            toast.error("Couldn't update user", {
              description: error.message || "An unknown error occurred",
            });
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
        },
      });
    }
  };

  return (
    <>
      <div className="flex h-full flex-col space-y-6 p-8">
        <PageHeader
          title="Users"
          description="Manage user accounts and permissions"
        />

        <div className="min-h-0 flex-1">
          <UsersTable
            data={usersData?.results || []}
            loading={isUsersLoading}
            className="h-full"
            onEditUser={handleEditUser}
            onDeleteUser={handleDeleteUser}
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
