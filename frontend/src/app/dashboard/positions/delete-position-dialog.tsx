import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface DeletePositionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  positionIgEpic: string;
  loading?: boolean;
}

export const DeletePositionDialog: React.FC<DeletePositionDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  positionIgEpic,
  loading = false,
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Close position</DialogTitle>
          <DialogDescription className="text-neutral-800">
            Are you sure you want to close position{" "}
            <span className="font-mono font-semibold">{positionIgEpic}</span>?
            This action cannot be undone and will permanently close the
            position.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={loading}>
            {loading ? "Closing..." : "Close Position"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
