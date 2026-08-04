/**
 * Cloudflare Worker + D1 adapter for the first-1,000 transition protocol.
 *
 * This module deliberately supports diagnostic canary mode only. The checked-in
 * configuration is disabled and unprovisioned. Production collection requires
 * a later founder decision and a reviewed code change.
 */

import {
  DEFINITION_VERSION,
  assertTransitionEnvelope,
} from "../qualifier.mjs";
import { digestMonthToken } from "../collector.mjs";


export const WORKER_IMPLEMENTATION_VERSION = 1;
export const CONTROL_REVISION = "audience-cloudflare-v1";
export const TRANSITION_PATH = "/v1/transition";
export const MAXIMUM_BODY_BYTES = 512;
export const ALLOWED_ORIGINS = Object.freeze([
  "https://davidsdailybread.com",
  "https://www.davidsdailybread.com",
]);

export const SQL = Object.freeze({
  insertFirstSeen: `
    INSERT OR IGNORE INTO audience_visitors (
      definition_version,
      month,
      token_digest,
      first_seen_date,
      expires_on
    ) VALUES (?1, ?2, ?3, ?4, date(?4, '+35 days'))
  `,
  recordReturned: `
    UPDATE audience_visitors
       SET returned_date = ?4
     WHERE definition_version = ?1
       AND month = ?2
       AND token_digest = ?3
       AND returned_date IS NULL
       AND first_seen_date < ?4
  `,
  recordQualified: `
    UPDATE audience_visitors
       SET qualified_date = ?4
     WHERE definition_version = ?1
       AND month = ?2
       AND token_digest = ?3
       AND qualified_date IS NULL
       AND returned_date IS NOT NULL
       AND returned_date < ?4
  `,
  readVisitor: `
    SELECT first_seen_date, returned_date, qualified_date
      FROM audience_visitors
     WHERE definition_version = ?1
       AND month = ?2
       AND token_digest = ?3
  `,
  purgeExpired: `
    DELETE FROM audience_visitors
     WHERE expires_on <= ?1
  `,
  countExpired: `
    SELECT COUNT(*) AS expired_count
      FROM audience_visitors
     WHERE expires_on <= ?1
  `,
  readAggregate: `
    SELECT first_seen_visitors,
           returning_visitors,
           qualified_engaged_returning_readers
      FROM audience_monthly_aggregates
     WHERE definition_version = ?1
       AND month = ?2
  `,
});

class RequestFailure extends Error {
  constructor(status, reason, headers = {}) {
    super(reason);
    this.status = status;
    this.reason = reason;
    this.headers = headers;
  }
}

function outcome(decision, reason, transition = null) {
  return { decision, reason, transition };
}

function responseHeaders(origin = null) {
  const headers = {
    "Cache-Control": "no-store, max-age=0",
    "Content-Type": "application/json; charset=utf-8",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
  };
  if (origin !== null) {
    headers["Access-Control-Allow-Origin"] = origin;
    headers.Vary = "Origin";
  }
  return headers;
}

function jsonOutcome(body, status, origin = null, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...responseHeaders(origin), ...extraHeaders },
  });
}

function allowedOrigin(request) {
  const origin = request.headers.get("Origin");
  if (!ALLOWED_ORIGINS.includes(origin)) {
    throw new RequestFailure(403, "origin-not-allowed");
  }
  return origin;
}

function assertExactRoute(url) {
  if (url.pathname !== TRANSITION_PATH) {
    throw new RequestFailure(404, "not-found");
  }
  if (url.search !== "") {
    throw new RequestFailure(400, "query-not-allowed");
  }
}

function assertCanaryConfiguration(env, url) {
  const healthy =
    env?.DDB_AUDIENCE_MODE === "canary" &&
    env?.DDB_CONTROL_REVISION === CONTROL_REVISION &&
    typeof env?.DDB_EXPECTED_HOST === "string" &&
    env.DDB_EXPECTED_HOST !== "" &&
    env.DDB_EXPECTED_HOST !== "UNSET" &&
    url.host === env.DDB_EXPECTED_HOST &&
    env?.DDB_BOT_CONTROL_VERIFIED === "true" &&
    env?.DDB_LOGGING_DISABLED_VERIFIED === "true" &&
    env?.DDB_RETENTION_CONTROL_VERIFIED === "true" &&
    env?.DDB_PURGE_ENABLED === "true" &&
    env?.AUDIENCE_DB &&
    typeof env.AUDIENCE_DB.prepare === "function" &&
    env?.AUDIENCE_REGISTRATION_LIMITER &&
    typeof env.AUDIENCE_REGISTRATION_LIMITER.limit === "function" &&
    typeof env?.DDB_CANARY_SECRET_SHA256 === "string" &&
    /^[a-f0-9]{64}$/.test(env.DDB_CANARY_SECRET_SHA256);
  if (!healthy) {
    throw new RequestFailure(503, "collection-disabled");
  }
}

async function sha256Hex(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function constantTimeHexEqual(left, right) {
  if (left.length !== right.length) return false;
  let difference = 0;
  for (let index = 0; index < left.length; index += 1) {
    difference |= left.charCodeAt(index) ^ right.charCodeAt(index);
  }
  return difference === 0;
}

async function assertCanaryAuthorization(request, expectedHash) {
  const secret = request.headers.get("X-DDB-Canary-Key");
  if (typeof secret !== "string" || secret.length < 32 || secret.length > 256) {
    throw new RequestFailure(401, "canary-authorization-required");
  }
  const actualHash = await sha256Hex(secret);
  if (!constantTimeHexEqual(actualHash, expectedHash)) {
    throw new RequestFailure(401, "canary-authorization-required");
  }
}

function assertJsonContentType(request) {
  if (request.headers.get("Content-Encoding") !== null) {
    throw new RequestFailure(415, "content-encoding-not-allowed");
  }
  const value = request.headers.get("Content-Type") || "";
  const parts = value.split(";").map((part) => part.trim().toLowerCase());
  if (parts[0] !== "application/json") {
    throw new RequestFailure(415, "content-type-not-allowed");
  }
  if (
    parts.length > 2 ||
    (parts.length === 2 && parts[1] !== "charset=utf-8")
  ) {
    throw new RequestFailure(415, "content-type-not-allowed");
  }
  const declaredLength = request.headers.get("Content-Length");
  if (
    declaredLength !== null &&
    (!/^[0-9]+$/.test(declaredLength) || Number(declaredLength) > MAXIMUM_BODY_BYTES)
  ) {
    throw new RequestFailure(413, "body-too-large");
  }
}

async function readBoundedBody(request) {
  if (request.body === null) {
    throw new RequestFailure(400, "invalid-envelope");
  }
  const reader = request.body.getReader();
  const chunks = [];
  let length = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    length += value.byteLength;
    if (length > MAXIMUM_BODY_BYTES) {
      await reader.cancel();
      throw new RequestFailure(413, "body-too-large");
    }
    chunks.push(value);
  }
  const bytes = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    throw new RequestFailure(400, "invalid-encoding");
  }
}

async function parseEnvelope(request) {
  const text = await readBoundedBody(request);
  let envelope;
  try {
    envelope = JSON.parse(text);
    assertTransitionEnvelope(envelope);
  } catch (error) {
    if (error instanceof RequestFailure) throw error;
    throw new RequestFailure(400, "invalid-envelope");
  }
  return envelope;
}

export function pacificReceiptDate(instant = new Date()) {
  if (!(instant instanceof Date) || Number.isNaN(instant.valueOf())) {
    throw new TypeError("trusted receipt time is invalid");
  }
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(instant);
  const byType = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  const date = `${byType.year}-${byType.month}-${byType.day}`;
  if (!/^[0-9]{4}-(0[1-9]|1[0-2])-[0-9]{2}$/.test(date)) {
    throw new TypeError("trusted receipt date is invalid");
  }
  return date;
}

function changedRows(result) {
  const changes = result?.meta?.changes;
  if (result?.success !== true || !Number.isInteger(changes) || changes < 0 || changes > 1) {
    throw new Error("D1 returned an invalid transition result");
  }
  return changes;
}

async function readVisitor(db, month, tokenDigest) {
  return db
    .prepare(SQL.readVisitor)
    .bind(DEFINITION_VERSION, month, tokenDigest)
    .first();
}

/** Execute one conditional transition. D1 triggers maintain the aggregates. */
export async function transitionWithD1(db, envelope, receivedDate) {
  assertTransitionEnvelope(envelope);
  if (
    typeof receivedDate !== "string" ||
    !/^[0-9]{4}-(0[1-9]|1[0-2])-[0-9]{2}$/.test(receivedDate)
  ) {
    throw new TypeError("trusted receipt date is invalid");
  }
  const parsedDate = new Date(`${receivedDate}T00:00:00Z`);
  if (
    Number.isNaN(parsedDate.valueOf()) ||
    parsedDate.toISOString().slice(0, 10) !== receivedDate
  ) {
    throw new TypeError("trusted receipt date is invalid");
  }
  if (!receivedDate.startsWith(`${envelope.month}-`)) {
    return outcome("rejected", "cross-month", envelope.transition);
  }
  const tokenDigest = await digestMonthToken({
    month: envelope.month,
    token: envelope.token,
  });
  const bindings = [
    DEFINITION_VERSION,
    envelope.month,
    tokenDigest,
    receivedDate,
  ];

  if (envelope.transition === "first-seen") {
    const result = await db.prepare(SQL.insertFirstSeen).bind(...bindings).run();
    return changedRows(result) === 1
      ? outcome("accepted", "registered", envelope.transition)
      : outcome("duplicate", "already-first-seen", envelope.transition);
  }

  if (envelope.transition === "returned") {
    const result = await db.prepare(SQL.recordReturned).bind(...bindings).run();
    if (changedRows(result) === 1) {
      return outcome("accepted", "return-recorded", envelope.transition);
    }
    const existing = await readVisitor(db, envelope.month, tokenDigest);
    if (existing === null) {
      return outcome("rejected", "missing-first-seen", envelope.transition);
    }
    if (existing.returned_date !== null) {
      return outcome("duplicate", "already-returned", envelope.transition);
    }
    return outcome("rejected", "same-day-return", envelope.transition);
  }

  const result = await db.prepare(SQL.recordQualified).bind(...bindings).run();
  if (changedRows(result) === 1) {
    return outcome("accepted", "qualification-recorded", envelope.transition);
  }
  const existing = await readVisitor(db, envelope.month, tokenDigest);
  if (existing === null) {
    return outcome("rejected", "missing-first-seen", envelope.transition);
  }
  if (existing.qualified_date !== null) {
    return outcome("duplicate", "already-qualified", envelope.transition);
  }
  if (existing.returned_date === null) {
    return outcome("rejected", "missing-returned", envelope.transition);
  }
  return outcome("rejected", "same-day-qualified", envelope.transition);
}

export async function readMonthlyAggregate(db, month) {
  const row = await db
    .prepare(SQL.readAggregate)
    .bind(DEFINITION_VERSION, month)
    .first();
  return {
    month,
    firstSeenVisitors: row?.first_seen_visitors ?? 0,
    returningVisitors: row?.returning_visitors ?? 0,
    qualifiedEngagedReturningReaders:
      row?.qualified_engaged_returning_readers ?? 0,
  };
}

export async function purgeExpiredRows(db, receivedDate) {
  const result = await db.prepare(SQL.purgeExpired).bind(receivedDate).run();
  const changes = result?.meta?.changes;
  if (result?.success !== true || !Number.isInteger(changes) || changes < 0) {
    throw new Error("D1 returned an invalid purge result");
  }
  const remaining = await db.prepare(SQL.countExpired).bind(receivedDate).first();
  if (!remaining || remaining.expired_count !== 0) {
    throw new Error("expired participant rows remain after purge");
  }
  return changes;
}

function knownVerifiedBot(request) {
  return request.cf?.botManagement?.verifiedBot === true;
}

async function registrationAllowed(env, receivedDate) {
  const result = await env.AUDIENCE_REGISTRATION_LIMITER.limit({
    key: `first-seen:${receivedDate}`,
  });
  if (!result || typeof result.success !== "boolean") {
    throw new Error("registration limiter returned an invalid result");
  }
  return result.success;
}

export async function handleRequest(request, env, options = {}) {
  let origin = null;
  try {
    const url = new URL(request.url);
    assertExactRoute(url);
    origin = allowedOrigin(request);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          ...responseHeaders(origin),
          "Access-Control-Allow-Headers": "Content-Type, X-DDB-Canary-Key",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Max-Age": "600",
        },
      });
    }
    if (request.method !== "POST") {
      throw new RequestFailure(405, "method-not-allowed", { Allow: "POST, OPTIONS" });
    }

    assertCanaryConfiguration(env, url);
    await assertCanaryAuthorization(request, env.DDB_CANARY_SECRET_SHA256);
    if (knownVerifiedBot(request)) {
      throw new RequestFailure(403, "known-bot");
    }
    assertJsonContentType(request);
    const envelope = await parseEnvelope(request);
    const receivedDate = pacificReceiptDate(options.now || new Date());
    if (envelope.month !== receivedDate.slice(0, 7)) {
      return jsonOutcome(
        outcome("rejected", "cross-month", envelope.transition),
        409,
        origin,
      );
    }
    if (
      envelope.transition === "first-seen" &&
      !(await registrationAllowed(env, receivedDate))
    ) {
      return jsonOutcome(
        outcome("rejected", "registration-blocked", envelope.transition),
        429,
        origin,
        { "Retry-After": "60" },
      );
    }
    const result = await transitionWithD1(env.AUDIENCE_DB, envelope, receivedDate);
    const status = result.decision === "rejected" ? 409 : 200;
    return jsonOutcome(result, status, origin);
  } catch (error) {
    if (error instanceof RequestFailure) {
      return jsonOutcome(
        outcome("rejected", error.reason),
        error.status,
        origin,
        error.headers,
      );
    }
    return jsonOutcome(outcome("rejected", "unavailable"), 503, origin);
  }
}

export default {
  fetch(request, env) {
    return handleRequest(request, env);
  },

  async scheduled(controller, env) {
    if (
      env?.DDB_AUDIENCE_MODE !== "canary" ||
      env?.DDB_CONTROL_REVISION !== CONTROL_REVISION ||
      env?.DDB_PURGE_ENABLED !== "true" ||
      env?.DDB_RETENTION_CONTROL_VERIFIED !== "true" ||
      !env?.AUDIENCE_DB
    ) {
      throw new Error("audience purge is disabled");
    }
    const receivedDate = pacificReceiptDate(new Date(controller.scheduledTime));
    await purgeExpiredRows(env.AUDIENCE_DB, receivedDate);
  },
};
