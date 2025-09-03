import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Copy, Check } from "lucide-react";
import { useCopyToClipboard } from "@/hooks/use-copy-to-clipboard";

export const Help = () => {
  const { copied, copy } = useCopyToClipboard();

  // Get the current hostname and construct the webhook URL
  const webhookUrl = `${window.location.origin}/api/v1/trading-view-webhook`;

  const handleCopyUrl = () => {
    copy(webhookUrl);
  };

  return (
    <div className="min-w-0 flex-1 space-y-8 p-8">
      <PageHeader
        title="Help"
        description="Important info and docs for the app"
      />

      <Card>
        <CardHeader className="-mb-6">
          <CardTitle className="flex items-center gap-2">
            TradingView Webhook URL
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-muted-foreground text-sm">
            Copy this URL and paste it into your TradingView alert webhook
            configuration:
          </p>

          <div className="bg-muted flex items-center gap-3 rounded-lg border p-3">
            <code className="text-foreground flex-1 font-mono text-sm break-all">
              {webhookUrl}
            </code>
            <Button
              size="sm"
              variant="default"
              onClick={handleCopyUrl}
              className="shrink-0"
            >
              {copied ? (
                <>
                  <Check className="size-4" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="size-4" />
                  Copy
                </>
              )}
            </Button>
          </div>

          <p className="text-muted-foreground text-xs">
            This webhook endpoint will receive trading signals from TradingView
            and execute trades automatically.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
