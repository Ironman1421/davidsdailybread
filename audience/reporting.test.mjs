import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { acceptEnvelope, createCollectorState } from "./collector.mjs";
import {
  MINIMAL_ENVELOPE_LIMITATION,
  PERSON_PROXY_LIMITATION,
  createMonthlyReportWithUnknownSupportingData,
  purgeCollectorState,
  reconcileMonthlyReport,
} from "./reporting.mjs";


const TOKEN = "AAAAAAAAAAAAAAAAAAAAAA";

function envelope(transition) {
  return {
    version: 1,
    definitionVersion: 1,
    month: "2026-08",
    transition,
    token: TOKEN,
  };
}

function gate(receivedDate) {
  return { receivedDate, registrationAllowed: true, knownBot: false };
}

async function qualifiedState() {
  let state = createCollectorState({ month: "2026-08" });
  for (const [transition, date] of [
    ["first-seen", "2026-08-01"],
    ["returned", "2026-08-02"],
    ["qualified", "2026-08-03"],
  ]) {
    ({ state } = await acceptEnvelope(state, envelope(transition), gate(date)));
  }
  return state;
}

function reportOptions(period = "2026-08") {
  const [year, month] = period.split("-").map(Number);
  const nextMonth = month === 12
    ? `${year + 1}-01`
    : `${year}-${String(month + 1).padStart(2, "0")}`;
  return {
    capturedAt: `${nextMonth}-01T08:00:00Z`,
    limitations: [],
    measurementStatus: "complete",
    sourceReceipt: `aggregate-receipt-${period}`,
  };
}

async function approvedLedger() {
  const ledger = JSON.parse(
    await readFile(new URL("./monthly-ledger.json", import.meta.url), "utf8"),
  );
  ledger.updatedAt = "2026-08-01T00:00:00Z";
  ledger.operatingState = "measuring";
  ledger.instrumentation = {
    status: "collecting",
    provider: "approved-local-first-collector-fixture",
    providerApprovedByDavid: true,
    externalProvisioningAuthorized: true,
    productionCollectionEnabled: true,
    spendAuthorizedUsd: 0,
    activationDate: "2026-08-01",
    sourceReceipt: "founder-approval-fixture",
  };
  ledger.milestoneEvidence = {
    status: "in-progress",
    achievedAt: null,
    qualifyingMonths: [],
  };
  return ledger;
}

function reportWithQualifiedCount(report, qualified) {
  return {
    ...report,
    metrics: {
      ...report.metrics,
      uniqueVisitors: qualified,
      returningVisitors: qualified,
      qualifiedEngagedReturningReaders: qualified,
    },
  };
}

test("monthly report contains aggregates and no visitor rows or token digests", async () => {
  const state = await qualifiedState();
  const report = createMonthlyReportWithUnknownSupportingData(
    state,
    reportOptions(),
  );
  assert.deepEqual(report.metrics, {
    uniqueVisitors: 1,
    returningVisitors: 1,
    qualifiedEngagedReturningReaders: 1,
    engagedSessions: null,
    medianActiveSecondsPerEngagedSession: null,
  });
  assert.equal(JSON.stringify(report).includes(TOKEN), false);
  assert.equal(JSON.stringify(report).includes("tokenDigest"), false);
  assert.equal(report.limitations.includes(PERSON_PROXY_LIMITATION), true);
  assert.equal(report.limitations.includes(MINIMAL_ENVELOPE_LIMITATION), true);
});

test("purge returns an empty collector state after aggregate capture", async () => {
  const purged = purgeCollectorState(await qualifiedState());
  assert.deepEqual(purged.recordsByTokenDigest, {});
});

test("ledger reconciliation fails closed without founder-approved measurement", async () => {
  const baseline = JSON.parse(
    await readFile(new URL("./monthly-ledger.json", import.meta.url), "utf8"),
  );
  const report = createMonthlyReportWithUnknownSupportingData(
    await qualifiedState(),
    reportOptions(),
  );
  assert.throws(
    () => reconcileMonthlyReport(baseline, report, { updatedAt: "2026-09-01T08:00:00Z" }),
    /founder-approved active measurement/,
  );
});

test("two consecutive complete target months produce achieved evidence", async () => {
  const ledger = await approvedLedger();
  const baseReport = reportWithQualifiedCount(
    createMonthlyReportWithUnknownSupportingData(
      createCollectorState({ month: "2026-08" }),
      reportOptions("2026-08"),
    ),
    1000,
  );
  let next = reconcileMonthlyReport(ledger, baseReport, {
    updatedAt: "2026-09-01T08:00:00Z",
  });
  assert.deepEqual(next.milestoneEvidence, {
    status: "in-progress",
    achievedAt: null,
    qualifyingMonths: ["2026-08"],
  });

  next = reconcileMonthlyReport(
    next,
    reportWithQualifiedCount(
      createMonthlyReportWithUnknownSupportingData(
        createCollectorState({ month: "2026-09" }),
        reportOptions("2026-09"),
      ),
      1000,
    ),
    { updatedAt: "2026-10-01T08:00:00Z" },
  );
  assert.deepEqual(next.milestoneEvidence, {
    status: "achieved",
    achievedAt: "2026-10-01T08:00:00Z",
    qualifyingMonths: ["2026-08", "2026-09"],
  });
});

test("a partial month cannot produce achieved evidence", async () => {
  const ledger = await approvedLedger();
  const complete = reportWithQualifiedCount(
    createMonthlyReportWithUnknownSupportingData(
      createCollectorState({ month: "2026-08" }),
      reportOptions("2026-08"),
    ),
    1000,
  );
  let next = reconcileMonthlyReport(ledger, complete, {
    updatedAt: "2026-09-01T08:00:00Z",
  });
  next = reconcileMonthlyReport(
    next,
    reportWithQualifiedCount(
      createMonthlyReportWithUnknownSupportingData(
        createCollectorState({ month: "2026-09" }),
        {
          ...reportOptions("2026-09"),
          measurementStatus: "partial",
        },
      ),
      1000,
    ),
    { updatedAt: "2026-10-01T08:00:00Z" },
  );
  assert.equal(next.milestoneEvidence.status, "in-progress");
});

test("ledger reconciliation rejects visitor rows and arbitrary report fields", async () => {
  const ledger = await approvedLedger();
  const report = createMonthlyReportWithUnknownSupportingData(
    createCollectorState({ month: "2026-08" }),
    reportOptions(),
  );
  assert.throws(
    () => reconcileMonthlyReport(
      ledger,
      { ...report, visitorRows: [{ tokenDigest: "forbidden" }] },
      { updatedAt: "2026-09-01T08:00:00Z" },
    ),
    /unexpected or missing fields/,
  );
});
