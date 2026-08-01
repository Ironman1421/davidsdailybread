import { ALLOWED_BROWSER_ORIGINS } from "../_shared/constants.ts";
import { newDeletionToken, sha256Hex } from "../_shared/crypto.ts";
import { submitSubmission } from "../_shared/database.ts";
import { safeError } from "../_shared/errors.ts";
import {
  browserError,
  browserJson,
  handleBrowserPreflight,
  readBrowserJson,
  requireBrowserPost,
} from "../_shared/http.ts";
import { logSafeEvent, requireEnabled } from "../_shared/runtime.ts";
import { verifyTurnstile } from "../_shared/turnstile.ts";
import { parseSubmissionInput } from "../_shared/validation.ts";

Deno.serve(async (request: Request): Promise<Response> => {
  const requestId = crypto.randomUUID();
  const requestOrigin = request.headers.get("Origin");
  const safeOrigin = ALLOWED_BROWSER_ORIGINS.includes(
      requestOrigin as (typeof ALLOWED_BROWSER_ORIGINS)[number],
    )
    ? requestOrigin
    : null;

  try {
    const preflight = handleBrowserPreflight(request);
    if (preflight !== null) return preflight;

    const origin = requireBrowserPost(request);
    requireEnabled("DDB_READER_SUBMIT_ENABLED");
    const input = parseSubmissionInput(await readBrowserJson(request));
    await verifyTurnstile(input.turnstileToken);

    const deletionToken = newDeletionToken();
    const deletionHash = await sha256Hex(deletionToken);
    const result = await submitSubmission(input, deletionHash);

    logSafeEvent("reader-submit", "accepted", requestId);
    return browserJson(origin, {
      status: "accepted",
      receipt: result.receipt,
      deletionToken,
    }, 201);
  } catch (error) {
    const safe = safeError(error);
    logSafeEvent("reader-submit", safe.code, requestId);
    return browserError(safeOrigin, safe);
  }
});
