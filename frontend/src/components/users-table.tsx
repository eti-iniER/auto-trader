import { VirtualizedTable } from "@/components/ui/virtualized-table";
import { formatDate } from "@/lib/formatting";
import { type ColumnDef } from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal, Edit, Trash2, FileX } from "lucide-react";

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
  onEditUser?: (user: UserAdminDetails) => void;
  onDeleteUser?: (user: UserAdminDetails) => void;
  onDeleteUserLogs?: (user: UserAdminDetails) => void;
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
  onEditUser,
  onDeleteUser,
  onDeleteUserLogs,
}: UsersTableProps) {
  // Create ActionsCell component
  const ActionsCell = ({ user }: { user: UserAdminDetails }) => (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="h-8 w-8 p-0">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => onEditUser?.(user)}>
          <Edit className="mr-2 h-4 w-4" />
          Edit user
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => onDeleteUserLogs?.(user)}>
          <FileX className="mr-2 h-4 w-4" />
          Delete user logs
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => onDeleteUser?.(user)}
          className="text-red-600 focus:text-red-600"
        >
          <Trash2 className="mr-2 h-4 w-4" />
          Delete user
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );

  // Add actions column to the existing columns
  const columnsWithActions: ColumnDef<UserAdminDetails>[] = [
    ...columns,
    {
      id: "actions",
      header: "Actions",
      size: 80,
      cell: ({ row }) => <ActionsCell user={row.original} />,
    },
  ];

  return (
    <VirtualizedTable
      data={data}
      columns={columnsWithActions}
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
