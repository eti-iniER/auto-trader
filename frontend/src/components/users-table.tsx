import { VirtualizedTable } from "@/components/ui/virtualized-table";
import { formatDate } from "@/lib/formatting";
import { type ColumnDef } from "@tanstack/react-table";

interface UsersTableProps {
  data: UserAdminDetails[];
  loading?: boolean;
  pagination?: {
    page: number;
    pageSize: number;
    totalCount: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (pageSize: number) => void;
  };
  className?: string;
  additionalInputs?: React.ReactNode;
}

const getRoleColor = (role: "USER" | "ADMIN") => {
  return role === "ADMIN"
    ? "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300"
    : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300";
};

const columns: ColumnDef<UserAdminDetails>[] = [
  {
    accessorKey: "firstName",
    header: "First Name",
    size: 150,
    cell: ({ row }) => (
      <div className="font-medium">{row.getValue("firstName")}</div>
    ),
  },
  {
    accessorKey: "lastName",
    header: "Last Name",
    size: 150,
    cell: ({ row }) => (
      <div className="font-medium">{row.getValue("lastName")}</div>
    ),
  },
  {
    accessorKey: "email",
    header: "Email",
    size: 250,
    cell: ({ row }) => (
      <div className="font-mono text-sm">{row.getValue("email")}</div>
    ),
  },
  {
    accessorKey: "role",
    header: "Role",
    size: 120,
    cell: ({ row }) => {
      const role = row.getValue("role") as "USER" | "ADMIN";
      return (
        <span
          className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${getRoleColor(role)}`}
        >
          {role}
        </span>
      );
    },
  },
  {
    accessorKey: "createdAt",
    header: "Created At",
    size: 180,
    cell: ({ row }) => {
      const createdAt = row.getValue("createdAt") as Date;
      return (
        <div className="text-sm text-gray-500">{formatDate(createdAt)}</div>
      );
    },
  },
  {
    accessorKey: "lastLogin",
    header: "Last Login",
    size: 180,
    cell: ({ row }) => {
      const lastLogin = row.getValue("lastLogin") as Date;
      return (
        <div className="text-sm text-gray-500">{formatDate(lastLogin)}</div>
      );
    },
  },
];

export function UsersTable({
  data,
  loading = false,
  pagination,
  className,
  additionalInputs,
}: UsersTableProps) {
  return (
    <VirtualizedTable
      data={data}
      columns={columns}
      loading={loading}
      pagination={pagination}
      className={className}
      additionalInputs={additionalInputs}
      searchPlaceholder="Search users by name or email..."
      rowHeight={50}
      fillAvailableHeight={true}
    />
  );
}
