import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface DeleteUserLogsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  userName: string;
  loading?: boolean;
}

export const DeleteUserLogsDialog: React.FC<DeleteUserLogsDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  userName,
  loading = false,
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete user logs</DialogTitle>
          <DialogDescription className="text-neutral-800">
            Are you sure you want to delete all logs for{" "}
            <span className="font-semibold">{userName}</span>? This action
            cannot be undone and will permanently remove all log entries
            associated with this user.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={loading}>
            {loading ? "Deleting..." : "Delete logs"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
