import type { Alert } from "@/hooks/useAlerts";
import { Button } from "@/components/ui/button";

interface AlertBannerProps {
  alerts: Alert[];
  onDismiss: (alertId: string) => void;
  onDismissAll: () => void;
}

const alertStyles: Record<Alert["type"], { bg: string; border: string; icon: string }> = {
  expiration: {
    bg: "bg-orange-50",
    border: "border-orange-200",
    icon: "\u23f0", // alarm clock
  },
  near_strike: {
    bg: "bg-yellow-50",
    border: "border-yellow-200",
    icon: "\u26a0\ufe0f", // warning
  },
  stale_price: {
    bg: "bg-gray-50",
    border: "border-gray-200",
    icon: "\u231b", // hourglass
  },
};

export default function AlertBanner({
  alerts,
  onDismiss,
  onDismissAll,
}: AlertBannerProps) {
  if (alerts.length === 0) return null;

  return (
    <div className="mb-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">
          {alerts.length} active alert{alerts.length !== 1 ? "s" : ""}
        </span>
        {alerts.length > 1 && (
          <Button variant="ghost" size="sm" onClick={onDismissAll}>
            Dismiss all
          </Button>
        )}
      </div>
      {alerts.map((alert) => {
        const style = alertStyles[alert.type];
        return (
          <div
            key={alert.id}
            className={`flex items-center justify-between rounded-md border px-3 py-2 text-sm ${style.bg} ${style.border}`}
          >
            <span>
              <span className="mr-2">{style.icon}</span>
              {alert.message}
            </span>
            <button
              type="button"
              className="ml-4 text-muted-foreground hover:text-foreground"
              onClick={() => onDismiss(alert.id)}
              aria-label="Dismiss alert"
            >
              &times;
            </button>
          </div>
        );
      })}
    </div>
  );
}
