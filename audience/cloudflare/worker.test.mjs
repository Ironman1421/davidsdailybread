import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  CONTROL_REVISION,
  SQL,
  handleRequest,
  pacificReceiptDate,
  purgeExpiredRows,
  readMonthlyAggregate,
  transitionWithD1,
} from "./worker.mjs";


const HOST = "ddb-audience-canary.example.workers.dev";
const ORIGIN = "https://davidsdailybread.com";
const TOKEN = "abcdefghijklmnopqrstuv";
const CANARY_SECRET = "local-canary-fixture-secret-value";

async function sha256Hex(value) {
  const digest = await globalThis.crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function plusDays(date, days) {
  const instant = new Date(`${date}T00:00:00Z`);
  instant.setUTCDate(instant.getUTCDate() + days);
  return instant.toISOString().slice(0, 10);
}

function rowKey(definitionVersion, month, digest) {
  return `${definitionVersion}:${month}:${digest}`;
}

function aggregateKey(definitionVersion, month) {
  return `${definitionVersion}:${month}`;
}

class FakeStatement {
  constructor(database, query) {
    this.database = database;
    this.query = query;
    this.values = [];
  }

  bind(...values) {
    this.values = values;
    return this;
  }

  async run() {
    return this.database.run(this.query, this.values);
  }

  async first() {
    return this.database.first(this.query, this.values);
  }
}

class FakeD1 {
  constructor() {
    this.visitors = new Map();
    this.aggregates = new Map();
    this.calls = 0;
  }

  prepare(query) {
    this.calls += 1;
    return new FakeStatement(this, query);
  }

  transitionResult(changes) {
    return { success: true, meta: { changes } };
  }

  aggregate(definitionVersion, month) {
    const key = aggregateKey(definitionVersion, month);
    if (!this.aggregates.has(key)) {
      this.aggregates.set(key, {
        first_seen_visitors: 0,
        returning_visitors: 0,
        qualified_engaged_returning_readers: 0,
      });
    }
    return this.aggregates.get(key);
  }

  async run(query, values) {
    const [definitionVersion, month, digest, receivedDate] = values;
    const key = rowKey(definitionVersion, month, digest);
    const existing = this.visitors.get(key);
    if (query === SQL.insertFirstSeen) {
      if (existing) return this.transitionResult(0);
      this.visitors.set(key, {
        first_seen_date: receivedDate,
        returned_date: null,
        qualified_date: null,
        expires_on: plusDays(receivedDate, 35),
      });
      this.aggregate(definitionVersion, month).first_seen_visitors += 1;
      return this.transitionResult(1);
    }
    if (query === SQL.recordReturned) {
      if (
        !existing ||
        existing.returned_date !== null ||
        existing.first_seen_date >= receivedDate
      ) {
        return this.transitionResult(0);
      }
      existing.returned_date = receivedDate;
      this.aggregate(definitionVersion, month).returning_visitors += 1;
      return this.transitionResult(1);
    }
    if (query === SQL.recordQualified) {
      if (
        !existing ||
        existing.qualified_date !== null ||
        existing.returned_date === null ||
        existing.returned_date >= receivedDate
      ) {
        return this.transitionResult(0);
      }
      existing.qualified_date = receivedDate;
      this.aggregate(
        definitionVersion,
        month,
      ).qualified_engaged_returning_readers += 1;
      return this.transitionResult(1);
    }
    if (query === SQL.purgeExpired) {
      let changes = 0;
      for (const [visitorKey, row] of this.visitors) {
        if (row.expires_on <= values[0]) {
          this.visitors.delete(visitorKey);
          changes += 1;
        }
      }
      return this.transitionResult(changes);
    }
    throw new Error("unexpected fake D1 run query");
  }

  async first(query, values) {
    if (query === SQL.readVisitor) {
      return this.visitors.get(rowKey(...values)) || null;
    }
    if (query === SQL.readAggregate) {
      return this.aggregates.get(aggregateKey(...values)) || null;
    }
    if (query === SQL.countExpired) {
      return {
        expired_count: [...this.visitors.values()].filter(
          (row) => row.expires_on <= values[0],
        ).length,
      };
    }
    throw new Error("unexpected fake D1 first query");
  }
}

function envelope(transition, month = "2026-07") {
  return {
    version: 1,
    definitionVersion: 1,
    month,
    transition,
    token: TOKEN,
  };
}

async function healthyEnvironment(database = new FakeD1()) {
  return {
    DDB_AUDIENCE_MODE: "canary",
    DDB_CONTROL_REVISION: CONTROL_REVISION,
    DDB_EXPECTED_HOST: HOST,
    DDB_BOT_CONTROL_VERIFIED: "true",
    DDB_LOGGING_DISABLED_VERIFIED: "true",
    DDB_RETENTION_CONTROL_VERIFIED: "true",
    DDB_PURGE_ENABLED: "true",
    DDB_CANARY_SECRET_SHA256: await sha256Hex(CANARY_SECRET),
    AUDIENCE_DB: database,
    AUDIENCE_REGISTRATION_LIMITER: {
      async limit() {
        return { success: true };
      },
    },
  };
}

function transitionRequest(transition, options = {}) {
  const body = options.body ?? JSON.stringify(envelope(transition, options.month));
  const request = new Request(
    options.url ?? `https://${HOST}/v1/transition`,
    {
      method: options.method ?? "POST",
      headers: {
        Origin: options.origin ?? ORIGIN,
        "Content-Type": options.contentType ?? "application/json",
        "X-DDB-Canary-Key": options.canaryKey ?? CANARY_SECRET,
      },
      body: options.method === "GET" ? undefined : body,
    },
  );
  if (options.verifiedBot) {
    Object.defineProperty(request, "cf", {
      value: { botManagement: { verifiedBot: true } },
    });
  }
  return request;
}

async function responseBody(response) {
  return JSON.parse(await response.text());
}

test("Pacific receipt dates respect both sides of the UTC month boundary", () => {
  assert.equal(pacificReceiptDate(new Date("2026-08-01T06:59:59Z")), "2026-07-31");
  assert.equal(pacificReceiptDate(new Date("2026-08-01T07:00:00Z")), "2026-08-01");
  assert.equal(pacificReceiptDate(new Date("2026-12-01T07:59:59Z")), "2026-11-30");
  assert.equal(pacificReceiptDate(new Date("2026-12-01T08:00:00Z")), "2026-12-01");
});

test("checked-in disabled state and every missing control fail before D1", async () => {
  const database = new FakeD1();
  const env = await healthyEnvironment(database);
  for (const field of [
    "DDB_AUDIENCE_MODE",
    "DDB_CONTROL_REVISION",
    "DDB_EXPECTED_HOST",
    "DDB_BOT_CONTROL_VERIFIED",
    "DDB_LOGGING_DISABLED_VERIFIED",
    "DDB_RETENTION_CONTROL_VERIFIED",
    "DDB_PURGE_ENABLED",
    "DDB_CANARY_SECRET_SHA256",
    "AUDIENCE_DB",
    "AUDIENCE_REGISTRATION_LIMITER",
  ]) {
    const incomplete = { ...env };
    delete incomplete[field];
    const response = await handleRequest(
      transitionRequest("first-seen"),
      incomplete,
      { now: new Date("2026-07-31T18:00:00Z") },
    );
    assert.equal(response.status, 503, field);
    assert.deepEqual(await responseBody(response), {
      decision: "rejected",
      reason: "collection-disabled",
      transition: null,
    });
  }
  assert.equal(database.calls, 0);
});

test("HTTP boundary rejects unauthorized and non-contract requests", async () => {
  const env = await healthyEnvironment();
  const cases = [
    [transitionRequest("first-seen", { origin: "https://example.com" }), 403],
    [transitionRequest("first-seen", { url: `https://${HOST}/wrong` }), 404],
    [transitionRequest("first-seen", { url: `https://${HOST}/v1/transition?token=x` }), 400],
    [transitionRequest("first-seen", { method: "GET" }), 405],
    [transitionRequest("first-seen", { canaryKey: "incorrect-secret-value-that-is-long-enough" }), 401],
    [transitionRequest("first-seen", { contentType: "text/plain" }), 415],
    [transitionRequest("first-seen", { body: "x".repeat(513) }), 413],
    [
      transitionRequest("first-seen", {
        body: JSON.stringify({ ...envelope("first-seen"), noteText: "never accepted" }),
      }),
      400,
    ],
  ];
  for (const [request, expectedStatus] of cases) {
    const response = await handleRequest(request, env, {
      now: new Date("2026-07-31T18:00:00Z"),
    });
    assert.equal(response.status, expectedStatus);
    const body = await responseBody(response);
    assert.deepEqual(Object.keys(body), ["decision", "reason", "transition"]);
    assert.equal(body.decision, "rejected");
  }
});

test("D1 transitions are ordered, distinct-day, idempotent, and aggregate-only", async () => {
  const database = new FakeD1();

  assert.deepEqual(
    await transitionWithD1(database, envelope("qualified"), "2026-07-03"),
    { decision: "rejected", reason: "missing-first-seen", transition: "qualified" },
  );
  assert.deepEqual(
    await transitionWithD1(database, envelope("first-seen"), "2026-07-01"),
    { decision: "accepted", reason: "registered", transition: "first-seen" },
  );
  assert.deepEqual(
    await transitionWithD1(database, envelope("first-seen"), "2026-07-01"),
    { decision: "duplicate", reason: "already-first-seen", transition: "first-seen" },
  );
  assert.equal(
    (await transitionWithD1(database, envelope("returned"), "2026-07-01")).reason,
    "same-day-return",
  );
  assert.equal(
    (await transitionWithD1(database, envelope("qualified"), "2026-07-02")).reason,
    "missing-returned",
  );
  assert.deepEqual(
    await transitionWithD1(database, envelope("returned"), "2026-07-02"),
    { decision: "accepted", reason: "return-recorded", transition: "returned" },
  );
  assert.equal(
    (await transitionWithD1(database, envelope("qualified"), "2026-07-02")).reason,
    "same-day-qualified",
  );
  assert.deepEqual(
    await transitionWithD1(database, envelope("qualified"), "2026-07-03"),
    { decision: "accepted", reason: "qualification-recorded", transition: "qualified" },
  );
  assert.equal(
    (await transitionWithD1(database, envelope("qualified"), "2026-07-04")).decision,
    "duplicate",
  );
  assert.deepEqual(await readMonthlyAggregate(database, "2026-07"), {
    month: "2026-07",
    firstSeenVisitors: 1,
    returningVisitors: 1,
    qualifiedEngagedReturningReaders: 1,
  });

  assert.equal(await purgeExpiredRows(database, "2026-08-05"), 1);
  assert.equal(database.visitors.size, 0);
  assert.deepEqual(await readMonthlyAggregate(database, "2026-07"), {
    month: "2026-07",
    firstSeenVisitors: 1,
    returningVisitors: 1,
    qualifiedEngagedReturningReaders: 1,
  });
});

test("handler rejects verified bots, exhausted registration, and cross-month envelopes", async () => {
  const env = await healthyEnvironment();
  let response = await handleRequest(
    transitionRequest("first-seen", { verifiedBot: true }),
    env,
    { now: new Date("2026-07-31T18:00:00Z") },
  );
  assert.equal(response.status, 403);
  assert.equal((await responseBody(response)).reason, "known-bot");

  env.AUDIENCE_REGISTRATION_LIMITER = {
    async limit() {
      return { success: false };
    },
  };
  response = await handleRequest(transitionRequest("first-seen"), env, {
    now: new Date("2026-07-31T18:00:00Z"),
  });
  assert.equal(response.status, 429);
  assert.equal((await responseBody(response)).reason, "registration-blocked");

  response = await handleRequest(
    transitionRequest("first-seen", { month: "2026-08" }),
    env,
    { now: new Date("2026-07-31T18:00:00Z") },
  );
  assert.equal(response.status, 409);
  assert.equal((await responseBody(response)).reason, "cross-month");
});

test("provider implementation contains no application logging or raw network identifier access", async () => {
  const source = await readFile(new URL("./worker.mjs", import.meta.url), "utf8");
  for (const forbidden of [
    "console.",
    "cf-connecting-ip",
    "CF-Connecting-IP",
    "request.headers.get(\"Referer\")",
    "request.headers.get(\"User-Agent\")",
    "request.headers.get(\"Cookie\")",
  ]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
  assert.equal(source.includes('DDB_AUDIENCE_MODE === "production"'), false);
});

test("unprovisioned template cannot expose or enable the Worker", async () => {
  const template = await readFile(
    new URL("./wrangler.unprovisioned.jsonc", import.meta.url),
    "utf8",
  );
  for (const required of [
    '"workers_dev": false',
    '"preview_urls": false',
    '"enabled": false',
    '"DDB_AUDIENCE_MODE": "disabled"',
    '"database_id": "UNPROVISIONED"',
    '"namespace_id": "UNPROVISIONED"',
  ]) {
    assert.equal(template.includes(required), true, required);
  }
  for (const forbidden of ["routes", "crons", "DDB_CANARY_SECRET_SHA256"]) {
    assert.equal(template.includes(`\"${forbidden}\"`), false, forbidden);
  }
});
