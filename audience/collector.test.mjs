import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  acceptEnvelope,
  aggregateCollectorState,
  assertCollectorState,
  createCollectorState,
  digestMonthToken,
} from "./collector.mjs";


const TOKEN_A = "AAAAAAAAAAAAAAAAAAAAAA";
const TOKEN_B = "BBBBBBBBBBBBBBBBBBBBBB";

function envelope(transition, { month = "2026-07", token = TOKEN_A } = {}) {
  return {
    version: 1,
    definitionVersion: 1,
    month,
    transition,
    token,
  };
}

function gate(receivedDate, overrides = {}) {
  return {
    receivedDate,
    registrationAllowed: true,
    knownBot: false,
    ...overrides,
  };
}

test("collector retains only a digest and aggregate status", async () => {
  const initial = createCollectorState({ month: "2026-07" });
  const result = await acceptEnvelope(
    initial,
    envelope("first-seen"),
    gate("2026-07-01"),
  );

  assert.deepEqual(result.outcome, {
    decision: "accepted",
    reason: "registered",
    transition: "first-seen",
  });
  assert.deepEqual(aggregateCollectorState(result.state), {
    month: "2026-07",
    firstSeenVisitors: 1,
    returningVisitors: 0,
    qualifiedEngagedReturningReaders: 0,
  });
  assert.equal(JSON.stringify(result).includes(TOKEN_A), false);
  assert.match(Object.keys(result.state.recordsByTokenDigest)[0], /^[a-f0-9]{64}$/);
});

test("collector enforces ordered transitions on separate server receipt days", async () => {
  let state = createCollectorState({ month: "2026-07" });

  let result = await acceptEnvelope(
    state,
    envelope("qualified"),
    gate("2026-07-01"),
  );
  assert.equal(result.outcome.reason, "missing-first-seen");
  state = result.state;

  result = await acceptEnvelope(state, envelope("first-seen"), gate("2026-07-01"));
  assert.equal(result.outcome.decision, "accepted");
  state = result.state;

  result = await acceptEnvelope(state, envelope("returned"), gate("2026-07-01"));
  assert.equal(result.outcome.reason, "same-day-return");
  state = result.state;

  result = await acceptEnvelope(state, envelope("returned"), gate("2026-07-02"));
  assert.equal(result.outcome.decision, "accepted");
  state = result.state;

  result = await acceptEnvelope(state, envelope("qualified"), gate("2026-07-02"));
  assert.equal(result.outcome.reason, "same-day-qualified");
  state = result.state;

  result = await acceptEnvelope(state, envelope("qualified"), gate("2026-07-03"));
  assert.equal(result.outcome.decision, "accepted");
  assert.deepEqual(aggregateCollectorState(result.state), {
    month: "2026-07",
    firstSeenVisitors: 1,
    returningVisitors: 1,
    qualifiedEngagedReturningReaders: 1,
  });
});

test("accepted transitions are idempotent", async () => {
  let state = createCollectorState({ month: "2026-07" });
  let result = await acceptEnvelope(state, envelope("first-seen"), gate("2026-07-01"));
  state = result.state;

  result = await acceptEnvelope(state, envelope("first-seen"), gate("2026-07-02"));
  assert.deepEqual(result.outcome, {
    decision: "duplicate",
    reason: "already-first-seen",
    transition: "first-seen",
  });
  assert.equal(Object.keys(result.state.recordsByTokenDigest).length, 1);

  result = await acceptEnvelope(result.state, envelope("returned"), gate("2026-07-02"));
  state = result.state;
  result = await acceptEnvelope(state, envelope("returned"), gate("2026-07-03"));
  assert.equal(result.outcome.reason, "already-returned");

  result = await acceptEnvelope(result.state, envelope("qualified"), gate("2026-07-03"));
  state = result.state;
  result = await acceptEnvelope(state, envelope("qualified"), gate("2026-07-04"));
  assert.equal(result.outcome.reason, "already-qualified");
});

test("collector rejects bot, blocked registration, and cross-month input", async () => {
  const initial = createCollectorState({ month: "2026-07" });

  const bot = await acceptEnvelope(
    initial,
    envelope("first-seen"),
    gate("2026-07-01", { knownBot: true }),
  );
  assert.equal(bot.outcome.reason, "known-bot");

  const blocked = await acceptEnvelope(
    initial,
    envelope("first-seen"),
    gate("2026-07-01", { registrationAllowed: false }),
  );
  assert.equal(blocked.outcome.reason, "registration-blocked");

  const crossMonth = await acceptEnvelope(
    initial,
    envelope("first-seen", { month: "2026-08" }),
    gate("2026-08-01"),
  );
  assert.equal(crossMonth.outcome.reason, "cross-month");
  assert.deepEqual(crossMonth.state.recordsByTokenDigest, {});
});

test("collector rejects closed-contract and invalid state input", async () => {
  const initial = createCollectorState({ month: "2026-07" });
  await assert.rejects(
    acceptEnvelope(
      initial,
      { ...envelope("first-seen"), pagePath: "/private" },
      gate("2026-07-01"),
    ),
    /unexpected or missing fields/,
  );
  await assert.rejects(
    acceptEnvelope(
      initial,
      envelope("first-seen"),
      { ...gate("2026-07-01"), ipAddress: "127.0.0.1" },
    ),
    /unexpected or missing fields/,
  );
  assert.throws(
    () => assertCollectorState({ ...initial, rawTokens: [TOKEN_A] }),
    /unexpected or missing fields/,
  );
});

test("token digest is deterministic and separates tokens", async () => {
  const digestA = await digestMonthToken({ month: "2026-07", token: TOKEN_A });
  assert.equal(
    digestA,
    await digestMonthToken({ month: "2026-07", token: TOKEN_A }),
  );
  assert.notEqual(
    digestA,
    await digestMonthToken({ month: "2026-07", token: TOKEN_B }),
  );
  assert.notEqual(
    digestA,
    await digestMonthToken({ month: "2026-08", token: TOKEN_A }),
  );
  assert.match(digestA, /^[a-f0-9]{64}$/);
});

test("collector source contains no transport, logging, or persistence primitive", async () => {
  const source = await readFile(new URL("./collector.mjs", import.meta.url), "utf8");
  for (const primitive of [
    "fetch(",
    "XMLHttpRequest",
    "sendBeacon",
    "WebSocket",
    "localStorage",
    "sessionStorage",
    "console.",
  ]) {
    assert.equal(source.includes(primitive), false, primitive);
  }
});
