import { constantTimeTextEqual } from "./crypto.ts";
import { SafeHttpError } from "./errors.ts";

export function requireEnabled(variableName: string): void {
  if (Deno.env.get(variableName) !== "true") {
    throw new SafeHttpError(503, "service_disabled");
  }
}

export function requireBrokerAuthentication(request: Request): void {
  const expectedToken = Deno.env.get("DDB_READER_BROKER_TOKEN") ?? "";
  if (expectedToken.length < 32 || expectedToken.length > 256) {
    throw new SafeHttpError(503, "service_unconfigured");
  }
  const supplied = request.headers.get("Authorization") ?? "";
  if (!constantTimeTextEqual(supplied, `Bearer ${expectedToken}`)) {
    throw new SafeHttpError(401, "unauthorized");
  }
}

export function logSafeEvent(
  functionName: "reader-submit" | "reader-delete" | "reader-plan",
  event: string,
  requestId: string,
): void {
  console.info(JSON.stringify({ function: functionName, event, requestId }));
}
