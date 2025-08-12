import type { APIError } from "@/lib/errors";

declare module "@tanstack/react-query" {
  interface Register {
    defaultError: APIError;
  }
}
