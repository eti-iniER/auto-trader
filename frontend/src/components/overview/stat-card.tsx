import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  description?: string;
  variant?: "default" | "success" | "warning";
}

export const StatCard = ({
  title,
  value,
  icon: Icon,
  description,
  variant = "default",
}: StatCardProps) => {
  const getVariantClasses = () => {
    switch (variant) {
      case "success":
        return "border-green-200 bg-green-50/50 dark:border-green-800/30 dark:bg-green-950/30";
      case "warning":
        return "border-orange-200 bg-orange-50/50 dark:border-orange-800/30 dark:bg-orange-950/30";
      default:
        return "";
    }
  };

  return (
    <Card className={`border shadow-none ${getVariantClasses()}`}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-muted-foreground text-sm font-medium">
            {title}
          </CardTitle>
          <Icon className="text-muted-foreground h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold">{value}</div>
        {description && (
          <p className="text-muted-foreground mt-1 text-xs">{description}</p>
        )}
      </CardContent>
    </Card>
  );
};
