import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileChartColumnIncreasing } from "lucide-react";
import { MdBarChart, MdCalendarToday } from "react-icons/md";

interface ActivityData {
  date: Date;
  epic: string;
  period: string;
  dealId: string;
  channel: string;
  type: string;
  status: string;
  description: string;
  details: Record<string, unknown> | null;
}

export interface ActivityCardProps {
  activities?: ActivityData[];
}

const ActivityItem = ({ activity }: { activity: ActivityData }) => {
  const getStatusBadgeVariant = (status: string) => {
    switch (status.toLowerCase()) {
      case "confirmed":
      case "success":
        return "default";
      case "pending":
        return "secondary";
      case "failed":
      case "rejected":
        return "destructive";
      default:
        return "outline";
    }
  };

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="hover:bg-accent/50 flex items-start justify-between rounded-lg border p-4 transition-colors">
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-center gap-2">
          <p className="truncate text-sm font-medium">{activity.epic}</p>
          <Badge
            variant={getStatusBadgeVariant(activity.status)}
            className="text-xs"
          >
            {activity.status}
          </Badge>
        </div>
        <p className="text-muted-foreground mb-1 truncate text-sm">
          {activity.description}
        </p>
        <div className="text-muted-foreground flex items-center gap-2 text-xs">
          <MdCalendarToday className="h-3 w-3" />
          <span>{formatDate(activity.date)}</span>
          <span>•</span>
          <span className="capitalize">{activity.type}</span>
        </div>
      </div>
    </div>
  );
};

export const ActivityCard = ({ activities }: ActivityCardProps) => {
  return (
    <Card className="flex h-full flex-col border shadow-none">
      <CardHeader className="flex-shrink-0">
        <div className="flex items-center gap-2">
          <MdBarChart className="h-5 w-5" />
          <CardTitle>Recent activity</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="min-h-0 flex-1">
        {!activities || activities.length === 0 ? (
          <div className="py-8 text-center">
            <FileChartColumnIncreasing className="text-muted-foreground/30 mx-auto mb-4 h-12 w-12" />
            <p className="text-muted-foreground text-sm">No recent activity</p>
            <p className="text-muted-foreground mt-1 text-xs">
              Your trading activities will appear here
            </p>
          </div>
        ) : (
          <div className="h-full space-y-3 overflow-y-auto">
            {activities.map((activity, index) => (
              <ActivityItem
                key={`${activity.dealId}-${index}`}
                activity={activity}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
