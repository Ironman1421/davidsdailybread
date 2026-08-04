import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  MEANINGFUL_ACTIONS,
  createMonthState,
  markTransitionSent,
  pendingTransitions,
  recordActiveReading,
  recordMeaningfulAction,
  recordVisit,
  rotateMonth,
  transitionEnvelope,
} from "./qualifier.mjs";


const MONTH_TOKEN = "0123456789ABCDEFGHijkl";
const NEXT_MONTH_TOKEN = "mnopqrstuvwxyzABCDEFGH";
const SESSION_ONE = "AAAAAAAAAAAAAAAAAAAAAA";
const SESSION_TWO = "BBBBBBBBBBBBBBBBBBBBBB";


test("machine constants match the governing monthly ledger", async () => {
  const ledger = JSON.parse(
    await readFile(new URL("./monthly-ledger.json", import.meta.url), "utf-8"),
  );
  const definition = ledger.milestoneDefinition;
  assert.equal(definition.minimumDistinctVisitDays, 3);
  assert.equal(definition.minimumEngagedSessions, 2);
  assert.equal(definition.minimumActiveReadingSeconds, 60);
  assert.deepEqual(MEANINGFUL_ACTIONS, definition.meaningfulActions);
});


test("three visit days and two engaged sessions produce one qualified transition", () => {
  let state = createMonthState({ month: "2026-08", token: MONTH_TOKEN });
  assert.deepEqual(pendingTransitions(state), []);

  state = recordVisit(state, { date: "2026-08-01" });
  assert.deepEqual(pendingTransitions(state), ["first-seen"]);
  assert.deepEqual(Object.keys(transitionEnvelope(state, "first-seen")).sort(), [
    "definitionVersion",
    "month",
    "token",
    "transition",
    "version",
  ]);
  state = markTransitionSent(state, "first-seen");
  assert.deepEqual(pendingTransitions(state), []);

  state = recordVisit(state, { date: "2026-08-03" });
  assert.deepEqual(pendingTransitions(state), ["returned"]);

  state = recordActiveReading(state, { sessionKey: SESSION_ONE, seconds: 59 });
  assert.equal(state.engagedSessionKeys.length, 0);
  state = recordActiveReading(state, { sessionKey: SESSION_ONE, seconds: 1 });
  assert.deepEqual(state.engagedSessionKeys, [SESSION_ONE]);

  state = recordMeaningfulAction(state, {
    sessionKey: SESSION_TWO,
    action: "reviewed-source-opened",
  });
  assert.deepEqual(state.engagedSessionKeys, [SESSION_ONE, SESSION_TWO]);
  assert.deepEqual(pendingTransitions(state), ["returned"]);

  state = recordVisit(state, { date: "2026-08-08" });
  assert.deepEqual(pendingTransitions(state), ["returned", "qualified"]);
  state = markTransitionSent(state, "returned");
  assert.deepEqual(pendingTransitions(state), ["qualified"]);

  const envelope = transitionEnvelope(state, "qualified");
  assert.deepEqual(envelope, {
    version: 1,
    definitionVersion: 1,
    month: "2026-08",
    transition: "qualified",
    token: MONTH_TOKEN,
  });
  state = markTransitionSent(state, "qualified");
  assert.deepEqual(pendingTransitions(state), []);
  assert.throws(() => markTransitionSent(state, "qualified"), /pending transition/);
});


test("a third day without two engaged sessions never qualifies", () => {
  let state = createMonthState({ month: "2026-08", token: MONTH_TOKEN });
  for (const date of ["2026-08-01", "2026-08-02", "2026-08-03"]) {
    state = recordVisit(state, { date });
  }
  state = recordMeaningfulAction(state, {
    sessionKey: SESSION_ONE,
    action: "rss-opened",
  });
  assert.deepEqual(pendingTransitions(state), ["first-seen", "returned"]);
  assert.throws(() => transitionEnvelope(state, "qualified"), /not currently pending/);
});


test("inputs are closed to exact dates, tokens, and meaningful actions", () => {
  const state = createMonthState({ month: "2026-08", token: MONTH_TOKEN });
  assert.throws(
    () => recordVisit(state, { date: "2026-08-32" }),
    /real calendar date/,
  );
  assert.throws(
    () => recordVisit(state, { date: "2026-09-01" }),
    /state month/,
  );
  assert.throws(
    () => recordMeaningfulAction(state, {
      sessionKey: SESSION_ONE,
      action: "arbitrary-free-text",
    }),
    /not allowlisted/,
  );
  assert.throws(
    () => createMonthState({ month: "2026-08", token: "too-short" }),
    /base64url/,
  );
});


test("month rotation retains no prior audience state", () => {
  let state = createMonthState({ month: "2026-08", token: MONTH_TOKEN });
  state = recordVisit(state, { date: "2026-08-31" });
  state = recordMeaningfulAction(state, {
    sessionKey: SESSION_ONE,
    action: "local-note-used",
  });

  const rotated = rotateMonth(state, {
    month: "2026-09",
    token: NEXT_MONTH_TOKEN,
  });
  assert.equal(rotated.month, "2026-09");
  assert.equal(rotated.token, NEXT_MONTH_TOKEN);
  assert.deepEqual(rotated.visitDates, []);
  assert.deepEqual(rotated.engagedSessionKeys, []);
  assert.deepEqual(rotated.activeSecondsBySession, {});
  assert.deepEqual(rotated.sentTransitions, []);
});


test("unfinished active-session bookkeeping stays locally bounded", () => {
  let state = createMonthState({ month: "2026-08", token: MONTH_TOKEN });
  for (let index = 0; index < 40; index += 1) {
    const sessionKey = index.toString(36).padStart(22, "A");
    state = recordActiveReading(state, { sessionKey, seconds: 1 });
  }
  assert.equal(Object.keys(state.activeSecondsBySession).length, 32);
});


test("prototype has no network implementation and is not loaded by site templates", async () => {
  const source = await readFile(new URL("./qualifier.mjs", import.meta.url), "utf-8");
  for (const forbidden of ["fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket"]) {
    assert.equal(source.includes(forbidden), false, `unexpected network primitive: ${forbidden}`);
  }

  for (const relativePath of ["../templates/home.html", "../templates/evening.html"]) {
    const template = await readFile(new URL(relativePath, import.meta.url), "utf-8");
    assert.equal(template.includes("audience/qualifier"), false);
  }
});
