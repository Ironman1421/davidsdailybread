import {
  ALLOWED_BROWSER_ORIGINS,
  TURNSTILE_EXPECTED_ACTION,
} from "./constants.ts";
import { SafeHttpError } from "./errors.ts";

interface TurnstileResult {
  success?: boolean;
  hostname?: string;
  action?: string;
}

const ALLOWED_HOSTNAMES = new Set(
  ALLOWED_BROWSER_ORIGINS.map((origin) => new URL(origin).hostname),
);

export async function verifyTurnstile(token: string): Promise<void> {
  const secret = Deno.env.get("DDB_TURNSTILE_SECRET_KEY") ?? "";
  if (secret.length < 1) throw new SafeHttpError(503, "service_unconfigured");

  const form = new URLSearchParams({ secret, response: token });
  let response: Response;
  try {
    response = await fetch(
      "https://challenges.cloudflare.com/turnstile/v0/siteverify",
      {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form,
        signal: AbortSignal.timeout(5_000),
      },
    );
  } catch {
    throw new SafeHttpError(503, "anti_abuse_unavailable");
  }

  if (!response.ok) throw new SafeHttpError(503, "anti_abuse_unavailable");

  let result: TurnstileResult;
  try {
    result = await response.json() as TurnstileResult;
  } catch {
    throw new SafeHttpError(503, "anti_abuse_unavailable");
  }

  if (
    result.success !== true ||
    typeof result.hostname !== "string" ||
    !ALLOWED_HOSTNAMES.has(result.hostname) ||
    result.action !== TURNSTILE_EXPECTED_ACTION
  ) {
    throw new SafeHttpError(400, "anti_abuse_failed");
  }
}
