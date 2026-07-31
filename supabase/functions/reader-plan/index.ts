import { authorizeHandoff, executePlan } from "../_shared/database.ts";
import { safeError } from "../_shared/errors.ts";
import {
  brokerError,
  brokerJson,
  readBrokerJson,
  requireBrokerPost,
} from "../_shared/http.ts";
import {
  logSafeEvent,
  requireBrokerAuthentication,
  requireEnabled,
} from "../_shared/runtime.ts";
import {
  cleanupExpiredHandoffs,
  createHandoffDownload,
  createHandoffUpload,
  deleteHandoff,
} from "../_shared/storage.ts";
import { parsePlanInput } from "../_shared/validation.ts";

Deno.serve(async (request: Request): Promise<Response> => {
  const requestId = crypto.randomUUID();
  try {
    requireBrokerPost(request);
    requireBrokerAuthentication(request);
    requireEnabled("DDB_READER_PLAN_ENABLED");
    const input = parsePlanInput(await readBrokerJson(request));
    let result: Record<string, unknown>;
    if (input.operation === "cleanup-handoffs") {
      result = await cleanupExpiredHandoffs();
    } else if (
      input.operation === "create-handoff-upload" ||
      input.operation === "create-handoff-download" ||
      input.operation === "delete-handoff"
    ) {
      const action = input.operation === "create-handoff-upload"
        ? "upload"
        : input.operation === "create-handoff-download"
        ? "download"
        : "delete";
      const { objectPath } = await authorizeHandoff(
        input.batchId,
        input.bundleDigest,
        action,
      );
      result = action === "upload"
        ? await createHandoffUpload(objectPath)
        : action === "download"
        ? await createHandoffDownload(objectPath)
        : await deleteHandoff(objectPath);
    } else {
      result = await executePlan(input);
    }
    logSafeEvent("reader-plan", `${input.operation}_success`, requestId);
    return brokerJson(result);
  } catch (error) {
    const safe = safeError(error);
    logSafeEvent("reader-plan", safe.code, requestId);
    return brokerError(safe);
  }
});
