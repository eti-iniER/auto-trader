import { useUsers } from "@/api/hooks/users/use-users";
import { PageHeader } from "@/components/page-header";
import { UsersTable } from "@/components/users-table";
import { useDashboardContext } from "@/hooks/contexts/use-dashboard-context";
import { Navigate } from "react-router";

export const Users: React.FC = () => {
  const { user } = useDashboardContext();
  const { data: usersData, isPending: isUsersLoading } = useUsers();

  // Check if user is admin, if not redirect them
  if (user.role !== "ADMIN") {
    return <Navigate to="/dashboard/overview" replace />;
  }

  return (
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
        />
      </div>
    </div>
  );
};
