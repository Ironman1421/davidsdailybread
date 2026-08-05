/**
 * Aggregate-only reporting boundary for the first-1,000 ledger.
 *
 * This module converts a validated collector state into a monthly aggregate
 * report. It does not read or write files, publish data, or retain visitor rows.
 */

import {
  aggregateCollectorState,
  assertCollectorState,
  createCollectorState,
} from "./collector.mjs";


export const PERSON_PROXY_LIMITATION =
  "A browser-scoped pseudonymous visitor is a proxy for a person across devices and shared browsers.";
export const MINIMAL_ENVELOPE_LIMITATION =
  "The minimal transition protocol intentionally does not transmit total engaged sessions or median active seconds; those aggregate fields remain unknown.";

const OPTION_KEYS = Object.freeze([
  "capturedAt",
  "exclusions",
  "limitations",
  "measurementStatus",
  "sourceReceipt",
  "supportingEvidence",
]);
const UNKNOWN_OPTION_KEYS = Object.freeze([
  "capturedAt",
  "limitations",
  "measurementStatus",
  "sourceReceipt",
]);
const REPORT_KEYS = Object.freeze([
  "capturedAt",
  "coverageStatus",
  "definitionVersion",
  "exclusions",
  "limitations",
  "measurementStatus",
  "metrics",
  "period",
  "sourceReceipt",
  "supportingEvidence",
]);
const METRIC_KEYS = Object.freeze([
  "engagedSessions",
  "medianActiveSecondsPerEngagedSession",
  "qualifiedEngagedReturningReaders",
  "returningVisitors",
  "uniqueVisitors",
]);
const SUPPORTING_KEYS = Object.freeze([
  "constructiveSocialParticipants",
  "editorialSlipsSubmitted",
  "repeatPublicDiscussionParticipants",
  "rssFollows",
  "rssRepeatRetrievals",
]);
const EXCLUSION_KEYS = Object.freeze([
  "internalVisits",
  "knownBots",
  "syntheticMonitorVisits",
]);
const DEFAULT_SUPPORTING_EVIDENCE = Object.freeze({
  rssFollows: null,
  rssRepeatRetrievals: null,
  constructiveSocialParticipants: null,
  editorialSlipsSubmitted: null,
  repeatPublicDiscussionParticipants: null,
});
const DEFAULT_EXCLUSIONS = Object.freeze({
  knownBots: null,
  internalVisits: null,
  syntheticMonitorVisits: null,
});

function assertExactKeys(value, expected, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new TypeError(`${label} must be an object`);
  }
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (JSON.stringify(actual) !== JSON.stringify(wanted)) {
    throw new TypeError(`${label} contains unexpected or missing fields`);
  }
}

function assertAggregateValues(value, expected, label) {
  assertExactKeys(value, expected, label);
  for (const [key, count] of Object.entries(value)) {
    if (count !== null && (!Number.isInteger(count) || count < 0)) {
      throw new TypeError(`${label}.${key} must be null or a non-negative integer`);
    }
  }
  return { ...value };
}

function assertCapturedAt(value) {
  if (
    typeof value !== "string" ||
    !/^[0-9]{4}-[0-9]{2}-[0-9]{2}T/.test(value) ||
    Number.isNaN(new Date(value).valueOf())
  ) {
    throw new TypeError("capturedAt must be an ISO date-time string");
  }
  return value;
}

function reportingMonthAt(value) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-US", {
      timeZone: "America/Los_Angeles",
      year: "numeric",
      month: "2-digit",
    })
      .formatToParts(new Date(value))
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value]),
  );
  return `${parts.year}-${parts.month}`;
}

function assertSourceReceipt(value) {
  if (
    typeof value !== "string" ||
    !/^[A-Za-z0-9._:-]{1,200}$/.test(value)
  ) {
    throw new TypeError("sourceReceipt must be an opaque aggregate receipt identifier");
  }
  return value;
}

function uniqueLimitations(limitations) {
  if (
    !Array.isArray(limitations) ||
    limitations.some((limitation) => typeof limitation !== "string" || !limitation.trim())
  ) {
    throw new TypeError("limitations must be an array of non-empty strings");
  }
  return [...new Set([
    ...limitations,
    PERSON_PROXY_LIMITATION,
    MINIMAL_ENVELOPE_LIMITATION,
  ])];
}

export function createMonthlyReport(state, options) {
  assertCollectorState(state);
  assertExactKeys(options, OPTION_KEYS, "monthly report options");
  if (!(["partial", "complete"].includes(options.measurementStatus))) {
    throw new TypeError("measurementStatus must be partial or complete");
  }
  assertCapturedAt(options.capturedAt);
  if (
    options.measurementStatus === "complete" &&
    monthNumber(reportingMonthAt(options.capturedAt)) <= monthNumber(state.month)
  ) {
    throw new TypeError("a complete report must be captured after its calendar month ends");
  }
  assertSourceReceipt(options.sourceReceipt);

  const aggregate = aggregateCollectorState(state);
  return {
    period: aggregate.month,
    definitionVersion: state.definitionVersion,
    measurementStatus: options.measurementStatus,
    coverageStatus: options.measurementStatus,
    capturedAt: options.capturedAt,
    sourceReceipt: options.sourceReceipt,
    metrics: {
      uniqueVisitors: aggregate.firstSeenVisitors,
      returningVisitors: aggregate.returningVisitors,
      qualifiedEngagedReturningReaders:
        aggregate.qualifiedEngagedReturningReaders,
      engagedSessions: null,
      medianActiveSecondsPerEngagedSession: null,
    },
    supportingEvidence: assertAggregateValues(
      options.supportingEvidence,
      SUPPORTING_KEYS,
      "supporting evidence",
    ),
    exclusions: assertAggregateValues(
      options.exclusions,
      EXCLUSION_KEYS,
      "exclusions",
    ),
    limitations: uniqueLimitations(options.limitations),
  };
}

export function createMonthlyReportWithUnknownSupportingData(
  state,
  options,
) {
  assertExactKeys(options, UNKNOWN_OPTION_KEYS, "unknown-data report options");
  const { capturedAt, limitations, measurementStatus, sourceReceipt } = options;
  return createMonthlyReport(state, {
    capturedAt,
    exclusions: DEFAULT_EXCLUSIONS,
    limitations,
    measurementStatus,
    sourceReceipt,
    supportingEvidence: DEFAULT_SUPPORTING_EVIDENCE,
  });
}

function monthNumber(period) {
  const [year, month] = period.split("-").map(Number);
  return year * 12 + month;
}

function milestoneEvidence(months, updatedAt, target) {
  const qualified = months
    .filter(
      (report) =>
        report.measurementStatus === "complete" &&
        report.coverageStatus === "complete" &&
        report.metrics.qualifiedEngagedReturningReaders >= target,
    )
    .map((report) => report.period);
  const pairs = qualified.slice(1).flatMap((later, index) => {
    const earlier = qualified[index];
    return monthNumber(later) - monthNumber(earlier) === 1
      ? [[earlier, later]]
      : [];
  });
  if (pairs.length) {
    return {
      status: "achieved",
      achievedAt: updatedAt,
      qualifyingMonths: pairs.at(-1),
    };
  }
  return {
    status: "in-progress",
    achievedAt: null,
    qualifyingMonths: qualified.length ? [qualified.at(-1)] : [],
  };
}

export function assertMonthlyReport(report) {
  assertExactKeys(report, REPORT_KEYS, "monthly report");
  if (!/^[0-9]{4}-(0[1-9]|1[0-2])$/.test(report.period)) {
    throw new TypeError("monthly report period must use YYYY-MM");
  }
  if (report.definitionVersion !== 1) {
    throw new TypeError("unsupported monthly report definition version");
  }
  if (!(["partial", "complete"].includes(report.measurementStatus))) {
    throw new TypeError("monthly report status must be partial or complete");
  }
  if (report.coverageStatus !== report.measurementStatus) {
    throw new TypeError("monthly report coverage and measurement status must match");
  }
  assertCapturedAt(report.capturedAt);
  if (
    report.measurementStatus === "complete" &&
    monthNumber(reportingMonthAt(report.capturedAt)) <= monthNumber(report.period)
  ) {
    throw new TypeError("a complete report must be captured after its calendar month ends");
  }
  assertSourceReceipt(report.sourceReceipt);

  assertExactKeys(report.metrics, METRIC_KEYS, "monthly report metrics");
  for (const key of [
    "uniqueVisitors",
    "returningVisitors",
    "qualifiedEngagedReturningReaders",
  ]) {
    if (!Number.isInteger(report.metrics[key]) || report.metrics[key] < 0) {
      throw new TypeError(`monthly report ${key} must be a non-negative integer`);
    }
  }
  if (
    report.metrics.qualifiedEngagedReturningReaders > report.metrics.returningVisitors ||
    report.metrics.returningVisitors > report.metrics.uniqueVisitors
  ) {
    throw new TypeError("monthly report must satisfy qualified <= returning <= unique");
  }
  const engagedSessions = report.metrics.engagedSessions;
  const medianSeconds = report.metrics.medianActiveSecondsPerEngagedSession;
  if (engagedSessions !== null && (!Number.isInteger(engagedSessions) || engagedSessions < 0)) {
    throw new TypeError("monthly report engagedSessions must be null or non-negative");
  }
  if (medianSeconds !== null && (!Number.isFinite(medianSeconds) || medianSeconds < 0)) {
    throw new TypeError("monthly report median active seconds must be null or non-negative");
  }
  assertAggregateValues(report.supportingEvidence, SUPPORTING_KEYS, "supporting evidence");
  assertAggregateValues(report.exclusions, EXCLUSION_KEYS, "exclusions");
  const limitations = uniqueLimitations(report.limitations);
  if (limitations.length !== report.limitations.length) {
    throw new TypeError("monthly report must include canonical limitations without duplicates");
  }
  return report;
}

export function reconcileMonthlyReport(ledger, report, options) {
  assertExactKeys(options, ["updatedAt"], "ledger reconciliation options");
  const { updatedAt } = options;
  if (!ledger || typeof ledger !== "object" || Array.isArray(ledger)) {
    throw new TypeError("ledger must be an object");
  }
  if (
    ledger.operatingState !== "measuring" ||
    ledger.instrumentation?.status !== "collecting" ||
    ledger.instrumentation?.providerApprovedByDavid !== true ||
    ledger.instrumentation?.externalProvisioningAuthorized !== true ||
    ledger.instrumentation?.productionCollectionEnabled !== true
  ) {
    throw new TypeError("ledger reconciliation requires founder-approved active measurement");
  }
  assertCapturedAt(updatedAt);
  assertMonthlyReport(report);
  for (const existingReport of ledger.months) assertMonthlyReport(existingReport);
  if (report.definitionVersion !== ledger.milestoneDefinition?.definitionVersion) {
    throw new TypeError("report and ledger definition versions must match");
  }
  if (
    !Number.isInteger(ledger.milestoneDefinition?.targetQualifiedReaders) ||
    ledger.milestoneDefinition.targetQualifiedReaders <= 0
  ) {
    throw new TypeError("ledger target must be a positive integer");
  }
  const next = structuredClone(ledger);
  next.updatedAt = updatedAt;
  next.months = next.months.filter((item) => item.period !== report.period);
  next.months.push(structuredClone(report));
  next.months.sort((left, right) => left.period.localeCompare(right.period));
  next.milestoneEvidence = milestoneEvidence(
    next.months,
    updatedAt,
    next.milestoneDefinition.targetQualifiedReaders,
  );
  return next;
}

export function purgeCollectorState(state) {
  assertCollectorState(state);
  return createCollectorState({ month: state.month });
}
