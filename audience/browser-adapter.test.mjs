import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  OPT_OUT_KEY,
  PERSISTENT_STATE_KEY,
  PRODUCTION_DEFAULTS,
  SESSION_KEY,
  createBrowserAdapter,
  generateRandomToken,
  reportingDateAt,
} from "./browser-adapter.mjs";


const TOKENS = [
  "AAAAAAAAAAAAAAAAAAAAAA",
  "BBBBBBBBBBBBBBBBBBBBBB",
  "CCCCCCCCCCCCCCCCCCCCCC",
  "DDDDDDDDDDDDDDDDDDDDDD",
];

function memoryStorage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
  };
}

function harness({
  now = "2026-07-01T19:00:00Z",
  deliveries = [],
  persistentStorage = memoryStorage(),
  sessionStorage = memoryStorage(),
  tokenFactory = null,
} = {}) {
  let current = new Date(now);
  let tokenIndex = 0;
  const listeners = new Map();
  const document = {
    visibilityState: "visible",
    addEventListener(name, listener) {
      listeners.set(name, listener);
    },
    removeEventListener(name) {
      listeners.delete(name);
    },
  };
  const dependencies = {
    clock: { now: () => new Date(current) },
    document,
    persistentStorage,
    sessionStorage,
    scheduler: {
      setInterval: () => 1,
      clearInterval: () => {},
    },
    tokenFactory: tokenFactory || (() => TOKENS[tokenIndex++]),
    deliverTransition: async (value) => {
      deliveries.push(value);
      return {
        decision: "accepted",
        reason: "fixture-accepted",
        transition: value.transition,
      };
    },
  };
  return {
    dependencies,
    deliveries,
    document,
    listeners,
    persistentStorage,
    sessionStorage,
    setNow(value) {
      current = new Date(value);
    },
  };
}

test("production configuration is disabled with no endpoint", async () => {
  const config = JSON.parse(
    await readFile(new URL("./browser-adapter.config.json", import.meta.url), "utf8"),
  );
  assert.deepEqual(config, PRODUCTION_DEFAULTS);
  assert.equal(config.enabled, false);
  assert.equal(config.endpoint, null);

  const adapter = createBrowserAdapter(null);
  assert.deepEqual(await adapter.start(), {
    enabled: false,
    started: false,
    optedOut: false,
    month: null,
    pendingTransitionCount: 0,
  });
  assert.throws(
    () => createBrowserAdapter(null, { enabled: false, endpoint: "/collect" }),
    /unexpected field/,
  );
});

test("reporting dates use America/Los_Angeles calendar boundaries", () => {
  assert.equal(reportingDateAt("2026-08-01T06:59:59Z"), "2026-07-31");
  assert.equal(reportingDateAt("2026-08-01T07:00:00Z"), "2026-08-01");
});

test("reference token generation uses exactly 128 random bits and base64url", () => {
  let requestedBytes = null;
  const token = generateRandomToken({
    getRandomValues(bytes) {
      requestedBytes = bytes.length;
      for (let index = 0; index < bytes.length; index += 1) bytes[index] = index;
      return bytes;
    },
  });
  assert.equal(requestedBytes, 16);
  assert.match(token, /^[A-Za-z0-9_-]{22}$/);
});

test("enabled adapter records a visit and emits only the narrow first-seen envelope", async () => {
  const context = harness();
  const adapter = createBrowserAdapter(context.dependencies, { enabled: true });
  await adapter.start();

  assert.equal(context.deliveries.length, 1);
  assert.deepEqual(Object.keys(context.deliveries[0]).sort(), [
    "definitionVersion",
    "month",
    "token",
    "transition",
    "version",
  ]);
  assert.equal(context.deliveries[0].transition, "first-seen");
  const stored = JSON.parse(context.persistentStorage.getItem(PERSISTENT_STATE_KEY));
  assert.deepEqual(stored.visitDates, ["2026-07-01"]);
  assert.equal(context.sessionStorage.getItem(SESSION_KEY), TOKENS[1]);
});

test("active reading counts only while visible and recently active", async () => {
  const context = harness();
  const adapter = createBrowserAdapter(context.dependencies, { enabled: true });
  await adapter.start();

  context.document.visibilityState = "hidden";
  await adapter.tick();
  let stored = JSON.parse(context.persistentStorage.getItem(PERSISTENT_STATE_KEY));
  assert.equal(stored.engagedSessionKeys.length, 0);

  context.document.visibilityState = "visible";
  for (let index = 0; index < 12; index += 1) await adapter.tick();
  stored = JSON.parse(context.persistentStorage.getItem(PERSISTENT_STATE_KEY));
  assert.equal(stored.engagedSessionKeys.length, 1);

  context.setNow("2026-07-01T19:00:31Z");
  await adapter.tick();
  stored = JSON.parse(context.persistentStorage.getItem(PERSISTENT_STATE_KEY));
  assert.equal(stored.engagedSessionKeys.length, 1);
});

test("meaningful actions are allowlisted and carry no content", async () => {
  const context = harness();
  const adapter = createBrowserAdapter(context.dependencies, { enabled: true });
  await adapter.start();
  await adapter.meaningfulAction("local-note-used");
  await assert.rejects(
    adapter.meaningfulAction("reader-wrote-private-text"),
    /not allowlisted/,
  );
  assert.equal(
    context.deliveries.some((delivery) => "noteText" in delivery),
    false,
  );
});

test("collector rejection remains pending for a later retry", async () => {
  const context = harness();
  context.dependencies.deliverTransition = async (value) => {
    context.deliveries.push(value);
    return {
      decision: "rejected",
      reason: "fixture-rejected",
      transition: value.transition,
    };
  };
  const adapter = createBrowserAdapter(context.dependencies, { enabled: true });
  const status = await adapter.start();
  assert.equal(status.pendingTransitionCount, 1);
  assert.deepEqual(
    JSON.parse(context.persistentStorage.getItem(PERSISTENT_STATE_KEY)).sentTransitions,
    [],
  );
});

test("malformed delivery outcomes fail closed without marking a transition", async () => {
  const context = harness();
  context.dependencies.deliverTransition = async () => ({
    decision: "accepted",
    unexpected: "field",
  });
  const adapter = createBrowserAdapter(context.dependencies, { enabled: true });
  await assert.rejects(adapter.start(), /unexpected or missing fields/);
  assert.deepEqual(
    JSON.parse(context.persistentStorage.getItem(PERSISTENT_STATE_KEY)).sentTransitions,
    [],
  );
});

test("three visit days and two separate engaged sessions emit qualification once", async () => {
  const persistentStorage = memoryStorage();
  const deliveries = [];
  let tokenIndex = 0;
  const tokenFactory = () => TOKENS[tokenIndex++];

  let context = harness({
    now: "2026-07-01T19:00:00Z",
    deliveries,
    persistentStorage,
    tokenFactory,
  });
  let adapter = createBrowserAdapter(context.dependencies, { enabled: true });
  await adapter.start();
  await adapter.meaningfulAction("local-note-used");
  adapter.stop();

  context = harness({
    now: "2026-07-02T19:00:00Z",
    deliveries,
    persistentStorage,
    tokenFactory,
  });
  adapter = createBrowserAdapter(context.dependencies, { enabled: true });
  await adapter.start();
  await adapter.meaningfulAction("rss-opened");
  adapter.stop();

  context = harness({
    now: "2026-07-03T19:00:00Z",
    deliveries,
    persistentStorage,
    tokenFactory,
  });
  adapter = createBrowserAdapter(context.dependencies, { enabled: true });
  await adapter.start();

  assert.deepEqual(
    deliveries.map((delivery) => delivery.transition),
    ["first-seen", "returned", "qualified"],
  );
});

test("opt-out stops operation and erases qualifier and session state", async () => {
  const context = harness();
  const adapter = createBrowserAdapter(context.dependencies, { enabled: true });
  await adapter.start();
  const status = adapter.setOptOut(true);
  assert.equal(status.optedOut, true);
  assert.equal(status.started, false);
  assert.equal(context.persistentStorage.getItem(OPT_OUT_KEY), "true");
  assert.equal(context.persistentStorage.getItem(PERSISTENT_STATE_KEY), null);
  assert.equal(context.sessionStorage.getItem(SESSION_KEY), null);

  const secondAdapter = createBrowserAdapter(context.dependencies, { enabled: true });
  const secondStatus = await secondAdapter.start();
  assert.equal(secondStatus.optedOut, true);
  assert.equal(secondStatus.started, false);
});

test("browser adapter has no endpoint, built-in transport, free-text, or template integration", async () => {
  const source = await readFile(new URL("./browser-adapter.mjs", import.meta.url), "utf8");
  for (const forbidden of [
    "fetch(",
    "XMLHttpRequest",
    "sendBeacon",
    "WebSocket",
    "noteText",
    "submissionContent",
  ]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
  for (const relativePath of ["../templates/home.html", "../templates/evening.html"]) {
    const template = await readFile(new URL(relativePath, import.meta.url), "utf8");
    assert.equal(template.includes("audience/browser-adapter"), false);
  }
});
