import { refreshToken } from "@/lib/authentication";
import { APIError } from "@/lib/errors";
import { revivers } from "@/lib/revivers";
import camelcaseKeys from "camelcase-keys";
import ky, { HTTPError } from "ky";

import snakecaseKeys from "snakecase-keys";

let isRefreshing = false;

export const api = ky.create({
  prefixUrl: import.meta.env.VITE_API_URL,
  timeout: 1000 * 60 * 5,
  credentials: "include",
  throwHttpErrors: true,
  parseJson: (text) => JSON.parse(text, revivers),
  hooks: {
    beforeRequest: [
      async (request) => {
        if (request.headers.get("Content-Type")?.includes("application/json")) {
          try {
            const bodyText = await request.text();
            if (bodyText) {
              const original = JSON.parse(bodyText);
              const snaked = snakecaseKeys(original, { deep: true });

              return new Request(request, { body: JSON.stringify(snaked) });
            }
          } catch {
            // If parsing fails, return the original request
          }
        }
        return request;
      },
    ],
    afterResponse: [
      async (_request, _options, response) => {
        // Trigger token refresh on unauthorized responses
        if (response.status === 401 && !isRefreshing) {
          isRefreshing = true;
          try {
            await refreshToken();
          } finally {
            isRefreshing = false;
          }
        }

        // Transform JSON responses to camelCase
        if (
          response.headers.get("Content-Type")?.includes("application/json")
        ) {
          try {
            const json = await response.json();
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const camel = camelcaseKeys(json as any, { deep: true });
            return new Response(JSON.stringify(camel), response);
          } catch {
            // If parsing fails, return the original response
            return response;
          }
        }

        return response;
      },
    ],

    beforeError: [
      async (error) => {
        if (error instanceof HTTPError) {
          try {
            const res = error.response;
            const data = await res.clone().json();

            if (
              typeof data?.code === "string" &&
              typeof data?.message === "string"
            ) {
              return new APIError(
                res,
                error.request,
                error.options,
                data.code,
                data.message,
                data.details || {},
              );
            }
          } catch {
            return error;
          }
        }
        return error;
      },
    ],
  },
});
