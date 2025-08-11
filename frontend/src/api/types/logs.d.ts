type LogType =
  | "UNSPECIFIED"
  | "AUTHENTICATION"
  | "ALERT"
  | "TRADE"
  | "ORDER"
  | "ERROR";

interface Log {
  createdAt: Date;
  message: string;
  description: string;
  type: LogType;
  extra: Record<string, string | number | boolean | null> | null;
}
