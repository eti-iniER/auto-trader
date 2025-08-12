type LogType =
  | "UNSPECIFIED"
  | "AUTHENTICATION"
  | "ALERT"
  | "TRADE"
  | "ORDER"
  | "ERROR";

type LogExtra = string | number | boolean | null | { [key: string]: LogExtra };

interface Log {
  id: string;
  createdAt: Date;
  message: string;
  description: string;
  type: LogType;
  extra: LogExtra;
}
