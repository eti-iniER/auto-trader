import { refreshToken } from "@/lib/authentication";
import { revivers } from "@/lib/revivers";
import camelcaseKeys from "camelcase-keys";
import ky from "ky";
import snakecaseKeys from "snakecase-keys";

let isRefreshing = false;

export const api = ky.create({
  prefixUrl: import.meta.env.VITE_API_URL,
  timeout: 1000 * 60 * 5,
  credentials: "include",
  parseJson: (text) => JSON.parse(text, revivers),
  hooks: {
    beforeRequest: [
      async (request, options) => {
        if (request.headers.get("Content-Type") === "application/json") {
          const json = await request.json();
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const snaked = snakecaseKeys(json as any, { deep: true });
          return new Request(request.url, {
            ...options,

            body: JSON.stringify(snaked),
          });
        }
      },
    ],
    afterResponse: [
      async (_request, _options, response) => {
        if (response.headers.get("Content-Type") === "application/json") {
          const json = await response.json();
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const camel = camelcaseKeys(json as any, { deep: true });
          return new Response(JSON.stringify(camel), response);
        }
      },
      async (_request, _options, response) => {
        if (response.status === 401 && !isRefreshing) {
          isRefreshing = true;
          try {
            await refreshToken();
          } finally {
            isRefreshing = false;
          }
        }
        return response;
      },
    ],
  },
});
