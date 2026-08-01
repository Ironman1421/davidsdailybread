export class SafeHttpError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string) {
    super(code);
    this.name = "SafeHttpError";
    this.status = status;
    this.code = code;
  }
}

export function safeError(error: unknown): SafeHttpError {
  if (error instanceof SafeHttpError) return error;

  const postgresCode =
    typeof error === "object" && error !== null && "code" in error
      ? String((error as { code: unknown }).code)
      : "";

  if (postgresCode === "22023") {
    return new SafeHttpError(400, "invalid_request");
  }
  if (postgresCode === "55000") return new SafeHttpError(409, "state_conflict");
  return new SafeHttpError(500, "internal_error");
}
