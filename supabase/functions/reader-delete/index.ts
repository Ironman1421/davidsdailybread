import { ALLOWED_BROWSER_ORIGINS } from "../_shared/constants.ts";
import { sha256Hex } from "../_shared/crypto.ts";
import { deleteSubmission } from "../_shared/database.ts";
import { safeError } from "../_shared/errors.ts";
import {
  browserError,
  browserJson,
  handleBrowserPreflight,
  readBrowserJson,
  requireBrowserPost,
} from "../_shared/http.ts";
import { logSafeEvent, requireEnabled } from "../_shared/runtime.ts";
import { parseDeletionInput } from "../_shared/validation.ts";

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
    requireEnabled("DDB_READER_DELETE_ENABLED");
    const deletionToken = parseDeletionInput(await readBrowserJson(request));
    const deletionHash = await sha256Hex(deletionToken);
    const result = await deleteSubmission(deletionHash);

    if (result.outcome === "public_removal_required") {
      logSafeEvent("reader-delete", "publication_boundary", requestId);
      return browserJson(origin, {
        status: "public_removal_required",
        removalProcess: "public-correction-or-removal",
      }, 409);
    }

    logSafeEvent("reader-delete", "accepted", requestId);
    return browserJson(origin, { status: "accepted" }, 202);
  } catch (error) {
    const safe = safeError(error);
    logSafeEvent("reader-delete", safe.code, requestId);
    return browserError(safeOrigin, safe);
  }
});
