/* eslint-disable @typescript-eslint/no-explicit-any */

import { HTTPError, type NormalizedOptions } from "ky";

export class APIError extends HTTPError {
  code: string;
  details: Record<string, any>;

  constructor(
    response: Response,
    request: Request,
    options: NormalizedOptions,
    code: string,
    message: string,
    details: any,
  ) {
    super(response, request, options);
    this.name = "APIError";
    this.code = code;
    this.message = message;
    this.details = details;
  }
}
