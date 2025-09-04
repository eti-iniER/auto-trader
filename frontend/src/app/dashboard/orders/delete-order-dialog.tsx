import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface DeleteOrderDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  orderIgEpic: string;
  loading?: boolean;
}

export const DeleteOrderDialog: React.FC<DeleteOrderDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  orderIgEpic,
  loading = false,
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete order</DialogTitle>
          <DialogDescription className="text-neutral-800">
            Are you sure you want to delete order{" "}
            <span className="font-mono font-semibold">{orderIgEpic}</span>? This
            action cannot be undone and will permanently remove the order from
            the system.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={loading}>
            {loading ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
