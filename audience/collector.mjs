/**
 * Pure collector state machine for local-first audience transitions.
 *
 * A future approved endpoint may call acceptEnvelope after transient bot and
 * registration-rate checks. This module performs no network, logging, storage,
 * account, or provider operations and never retains the raw month token.
 */

import {
  DEFINITION_VERSION,
  QUALIFIER_VERSION,
  assertTransitionEnvelope,
} from "./qualifier.mjs";


export const COLLECTOR_VERSION = 1;
export const REPORTING_TIME_ZONE = "America/Los_Angeles";

const COLLECTOR_KEYS = Object.freeze([
  "definitionVersion",
  "month",
  "recordsByTokenDigest",
  "reportingTimeZone",
  "version",
]);
const RECORD_KEYS = Object.freeze([
  "firstSeenDate",
  "month",
  "qualifiedDate",
  "returnedDate",
  "status",
  "tokenDigest",
]);
const GATE_KEYS = Object.freeze([
  "knownBot",
  "receivedDate",
  "registrationAllowed",
]);
const MONTH_PATTERN = /^[0-9]{4}-(0[1-9]|1[0-2])$/;
const DATE_PATTERN = /^[0-9]{4}-(0[1-9]|1[0-2])-[0-9]{2}$/;
const DIGEST_PATTERN = /^[a-f0-9]{64}$/;

function assertExactKeys(value, expected, label) {
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (JSON.stringify(actual) !== JSON.stringify(wanted)) {
    throw new TypeError(`${label} contains unexpected or missing fields`);
  }
}

function assertMonth(month) {
  if (typeof month !== "string" || !MONTH_PATTERN.test(month)) {
    throw new TypeError("collector month must use YYYY-MM");
  }
}

function assertCalendarDate(date) {
  if (typeof date !== "string" || !DATE_PATTERN.test(date)) {
    throw new TypeError("collector receipt date must use YYYY-MM-DD");
  }
  const parsed = new Date(`${date}T00:00:00Z`);
  if (Number.isNaN(parsed.valueOf()) || parsed.toISOString().slice(0, 10) !== date) {
    throw new TypeError("collector receipt date must be a real calendar date");
  }
}

function assertDate(date, month) {
  assertCalendarDate(date);
  if (!date.startsWith(`${month}-`)) {
    throw new TypeError("collector receipt date must belong to the collector month");
  }
}

function assertDigest(digest) {
  if (typeof digest !== "string" || !DIGEST_PATTERN.test(digest)) {
    throw new TypeError("token digest must be a lowercase SHA-256 hex value");
  }
}

function assertRecord(record, expectedMonth, expectedDigest) {
  if (!record || typeof record !== "object" || Array.isArray(record)) {
    throw new TypeError("collector record must be an object");
  }
  assertExactKeys(record, RECORD_KEYS, "collector record");
  assertMonth(record.month);
  if (record.month !== expectedMonth) {
    throw new TypeError("collector record month does not match its state");
  }
  assertDigest(record.tokenDigest);
  if (record.tokenDigest !== expectedDigest) {
    throw new TypeError("collector record digest does not match its key");
  }
  assertDate(record.firstSeenDate, record.month);
  if (record.returnedDate !== null) {
    assertDate(record.returnedDate, record.month);
    if (record.returnedDate <= record.firstSeenDate) {
      throw new TypeError("returned date must follow first-seen date");
    }
  }
  if (record.qualifiedDate !== null) {
    assertDate(record.qualifiedDate, record.month);
    if (record.returnedDate === null || record.qualifiedDate <= record.returnedDate) {
      throw new TypeError("qualified date must follow returned date");
    }
  }
  const expectedStatus = record.qualifiedDate
    ? "qualified"
    : record.returnedDate
      ? "returned"
      : "first-seen";
  if (record.status !== expectedStatus) {
    throw new TypeError("collector record status does not match its dates");
  }
}

export function assertCollectorState(state) {
  if (!state || typeof state !== "object" || Array.isArray(state)) {
    throw new TypeError("collector state must be an object");
  }
  assertExactKeys(state, COLLECTOR_KEYS, "collector state");
  if (state.version !== COLLECTOR_VERSION) {
    throw new TypeError("unsupported collector version");
  }
  if (state.definitionVersion !== DEFINITION_VERSION) {
    throw new TypeError("unsupported collector definition version");
  }
  if (state.reportingTimeZone !== REPORTING_TIME_ZONE) {
    throw new TypeError("collector reporting time zone is not canonical");
  }
  assertMonth(state.month);
  if (
    !state.recordsByTokenDigest ||
    typeof state.recordsByTokenDigest !== "object" ||
    Array.isArray(state.recordsByTokenDigest)
  ) {
    throw new TypeError("collector records must be an object");
  }
  for (const [digest, record] of Object.entries(state.recordsByTokenDigest)) {
    assertDigest(digest);
    assertRecord(record, state.month, digest);
  }
  return state;
}

function cloneState(state) {
  assertCollectorState(state);
  return {
    ...state,
    recordsByTokenDigest: Object.fromEntries(
      Object.entries(state.recordsByTokenDigest).map(([digest, record]) => [
        digest,
        { ...record },
      ]),
    ),
  };
}

export function createCollectorState({ month }) {
  const state = {
    version: COLLECTOR_VERSION,
    definitionVersion: DEFINITION_VERSION,
    reportingTimeZone: REPORTING_TIME_ZONE,
    month,
    recordsByTokenDigest: {},
  };
  return assertCollectorState(state);
}

export async function digestMonthToken({ month, token }) {
  assertTransitionEnvelope({
    version: QUALIFIER_VERSION,
    definitionVersion: DEFINITION_VERSION,
    month,
    transition: "first-seen",
    token,
  });
  const bytes = new TextEncoder().encode(`${DEFINITION_VERSION}:${month}:${token}`);
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function outcome(decision, reason, transition) {
  return { decision, reason, transition };
}

function acceptDigestTransition(state, envelope, gate, tokenDigest) {
  const next = cloneState(state);
  assertTransitionEnvelope(envelope);
  if (!gate || typeof gate !== "object" || Array.isArray(gate)) {
    throw new TypeError("collector gate must be an object");
  }
  assertExactKeys(gate, GATE_KEYS, "collector gate");
  if (typeof gate.registrationAllowed !== "boolean" || typeof gate.knownBot !== "boolean") {
    throw new TypeError("collector gate flags must be boolean");
  }
  assertCalendarDate(gate.receivedDate);
  assertDigest(tokenDigest);

  if (envelope.month !== next.month) {
    return { state: next, outcome: outcome("rejected", "cross-month", envelope.transition) };
  }
  assertDate(gate.receivedDate, next.month);
  if (gate.knownBot) {
    return { state: next, outcome: outcome("rejected", "known-bot", envelope.transition) };
  }

  const existing = next.recordsByTokenDigest[tokenDigest];
  if (envelope.transition === "first-seen") {
    if (existing) {
      return { state: next, outcome: outcome("duplicate", "already-first-seen", envelope.transition) };
    }
    if (!gate.registrationAllowed) {
      return { state: next, outcome: outcome("rejected", "registration-blocked", envelope.transition) };
    }
    next.recordsByTokenDigest[tokenDigest] = {
      month: next.month,
      tokenDigest,
      firstSeenDate: gate.receivedDate,
      returnedDate: null,
      qualifiedDate: null,
      status: "first-seen",
    };
    return {
      state: assertCollectorState(next),
      outcome: outcome("accepted", "registered", envelope.transition),
    };
  }

  if (!existing) {
    return { state: next, outcome: outcome("rejected", "missing-first-seen", envelope.transition) };
  }

  if (envelope.transition === "returned") {
    if (existing.returnedDate !== null) {
      return { state: next, outcome: outcome("duplicate", "already-returned", envelope.transition) };
    }
    if (gate.receivedDate <= existing.firstSeenDate) {
      return { state: next, outcome: outcome("rejected", "same-day-return", envelope.transition) };
    }
    existing.returnedDate = gate.receivedDate;
    existing.status = "returned";
    return {
      state: assertCollectorState(next),
      outcome: outcome("accepted", "return-recorded", envelope.transition),
    };
  }

  if (existing.qualifiedDate !== null) {
    return { state: next, outcome: outcome("duplicate", "already-qualified", envelope.transition) };
  }
  if (existing.returnedDate === null) {
    return { state: next, outcome: outcome("rejected", "missing-returned", envelope.transition) };
  }
  if (gate.receivedDate <= existing.returnedDate) {
    return { state: next, outcome: outcome("rejected", "same-day-qualified", envelope.transition) };
  }
  existing.qualifiedDate = gate.receivedDate;
  existing.status = "qualified";
  return {
    state: assertCollectorState(next),
    outcome: outcome("accepted", "qualification-recorded", envelope.transition),
  };
}

export async function acceptEnvelope(state, envelope, gate) {
  assertTransitionEnvelope(envelope);
  const tokenDigest = await digestMonthToken({
    month: envelope.month,
    token: envelope.token,
  });
  return acceptDigestTransition(state, envelope, gate, tokenDigest);
}

export function aggregateCollectorState(state) {
  assertCollectorState(state);
  const records = Object.values(state.recordsByTokenDigest);
  return {
    month: state.month,
    firstSeenVisitors: records.length,
    returningVisitors: records.filter((record) => record.returnedDate !== null).length,
    qualifiedEngagedReturningReaders: records.filter(
      (record) => record.qualifiedDate !== null,
    ).length,
  };
}
