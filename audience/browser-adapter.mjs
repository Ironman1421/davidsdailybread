/**
 * Disabled-by-default browser boundary for the local-first qualifier.
 *
 * This module is deliberately not imported by a public template. It has no
 * endpoint and no built-in transport. A future approved integration must
 * inject a delivery function and opt in with enabled=true after the founder
 * activation gate is complete.
 */

import {
  assertQualifierState,
  assertSessionKey,
  createMonthState,
  markTransitionSent,
  pendingTransitions,
  recordActiveReading,
  recordMeaningfulAction,
  recordVisit,
  rotateMonth,
  transitionEnvelope,
} from "./qualifier.mjs";


export const BROWSER_ADAPTER_VERSION = 1;
export const REPORTING_TIME_ZONE = "America/Los_Angeles";
export const IDLE_AFTER_SECONDS = 30;
export const TICK_SECONDS = 5;
export const PERSISTENT_STATE_KEY = "ddb.audience.v1";
export const SESSION_KEY = "ddb.audience.session.v1";
export const OPT_OUT_KEY = "ddb.audience.optout.v1";
export const PRODUCTION_DEFAULTS = Object.freeze({
  version: BROWSER_ADAPTER_VERSION,
  enabled: false,
  endpoint: null,
  reportingTimeZone: REPORTING_TIME_ZONE,
  idleAfterSeconds: IDLE_AFTER_SECONDS,
  tickSeconds: TICK_SECONDS,
  tokenRandomBits: 128,
  persistentStateKey: PERSISTENT_STATE_KEY,
  sessionKey: SESSION_KEY,
  optOutKey: OPT_OUT_KEY,
});

const ACTIVITY_EVENTS = Object.freeze(["keydown", "pointerdown", "scroll", "touchstart"]);
const DELIVERY_OUTCOME_KEYS = Object.freeze(["decision", "reason", "transition"]);
const DELIVERY_DECISIONS = Object.freeze(["accepted", "duplicate", "rejected"]);
const BASE64URL_ALPHABET =
  "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

function requireMethod(value, method, label) {
  if (!value || typeof value[method] !== "function") {
    throw new TypeError(`${label} must provide ${method}()`);
  }
}

function requireDependencies(dependencies) {
  if (!dependencies || typeof dependencies !== "object" || Array.isArray(dependencies)) {
    throw new TypeError("browser adapter dependencies must be an object");
  }
  const {
    clock,
    document,
    persistentStorage,
    scheduler,
    sessionStorage,
    tokenFactory,
  } = dependencies;
  requireMethod(clock, "now", "clock");
  requireMethod(document, "addEventListener", "document");
  requireMethod(document, "removeEventListener", "document");
  for (const [storage, label] of [
    [persistentStorage, "persistent storage"],
    [sessionStorage, "session storage"],
  ]) {
    requireMethod(storage, "getItem", label);
    requireMethod(storage, "setItem", label);
    requireMethod(storage, "removeItem", label);
  }
  requireMethod(scheduler, "setInterval", "scheduler");
  requireMethod(scheduler, "clearInterval", "scheduler");
  if (typeof tokenFactory !== "function") {
    throw new TypeError("tokenFactory must be a function");
  }
}

export function reportingDateAt(value) {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.valueOf())) {
    throw new TypeError("clock value must be a valid date");
  }
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-US", {
      timeZone: REPORTING_TIME_ZONE,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    })
      .formatToParts(date)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}`;
}

export function generateRandomToken(randomSource) {
  requireMethod(randomSource, "getRandomValues", "random source");
  const bytes = new Uint8Array(16);
  randomSource.getRandomValues(bytes);
  let token = "";
  let accumulator = 0;
  let bitCount = 0;
  for (const byte of bytes) {
    accumulator = (accumulator << 8) | byte;
    bitCount += 8;
    while (bitCount >= 6) {
      bitCount -= 6;
      token += BASE64URL_ALPHABET[(accumulator >> bitCount) & 63];
      accumulator &= (1 << bitCount) - 1;
    }
  }
  if (bitCount) token += BASE64URL_ALPHABET[(accumulator << (6 - bitCount)) & 63];
  assertSessionKey(token);
  return token;
}

function parseState(raw) {
  if (typeof raw !== "string") return null;
  try {
    return assertQualifierState(JSON.parse(raw));
  } catch {
    return null;
  }
}

function acceptedByCollector(result, expectedTransition) {
  if (!result || typeof result !== "object" || Array.isArray(result)) {
    throw new TypeError("delivery outcome must be an object");
  }
  const actualKeys = Object.keys(result).sort();
  if (JSON.stringify(actualKeys) !== JSON.stringify([...DELIVERY_OUTCOME_KEYS].sort())) {
    throw new TypeError("delivery outcome contains unexpected or missing fields");
  }
  if (!DELIVERY_DECISIONS.includes(result.decision)) {
    throw new TypeError("delivery outcome contains an unknown decision");
  }
  if (typeof result.reason !== "string" || !result.reason) {
    throw new TypeError("delivery outcome reason must be a non-empty string");
  }
  if (result.transition !== expectedTransition) {
    throw new TypeError("delivery outcome transition does not match its request");
  }
  return result.decision === "accepted" || result.decision === "duplicate";
}

export function createBrowserAdapter(dependencies, options = {}) {
  if (!options || typeof options !== "object" || Array.isArray(options)) {
    throw new TypeError("browser adapter options must be an object");
  }
  if (Object.keys(options).some((key) => key !== "enabled")) {
    throw new TypeError("browser adapter options contain an unexpected field");
  }
  const { enabled = false } = options;
  if (typeof enabled !== "boolean") {
    throw new TypeError("enabled must be boolean");
  }

  let started = false;
  let optedOut = false;
  let state = null;
  let sessionKey = null;
  let intervalHandle = null;
  let lastActivityAt = null;
  let flushQueue = Promise.resolve();

  function status() {
    return {
      enabled,
      started,
      optedOut,
      month: state?.month ?? null,
      pendingTransitionCount: state ? pendingTransitions(state).length : 0,
    };
  }

  function persist() {
    dependencies.persistentStorage.setItem(PERSISTENT_STATE_KEY, JSON.stringify(state));
  }

  function eraseLocalMeasurementState() {
    dependencies.persistentStorage.removeItem(PERSISTENT_STATE_KEY);
    dependencies.sessionStorage.removeItem(SESSION_KEY);
    state = null;
    sessionKey = null;
  }

  function replaceSessionKey() {
    sessionKey = dependencies.tokenFactory();
    dependencies.sessionStorage.setItem(SESSION_KEY, sessionKey);
  }

  function rotateIfNeeded(date) {
    const month = date.slice(0, 7);
    if (state.month !== month) {
      state = rotateMonth(state, { month, token: dependencies.tokenFactory() });
      replaceSessionKey();
    }
  }

  async function flush() {
    if (!started || optedOut || !state) return status();
    for (const transition of pendingTransitions(state)) {
      const result = await dependencies.deliverTransition(
        transitionEnvelope(state, transition),
      );
      if (!acceptedByCollector(result, transition)) break;
      state = markTransitionSent(state, transition);
      persist();
    }
    return status();
  }

  function queueFlush() {
    flushQueue = flushQueue.then(flush, flush);
    return flushQueue;
  }

  function noteActivity() {
    if (started && !optedOut) lastActivityAt = dependencies.clock.now();
  }

  function stop() {
    if (!started) return status();
    dependencies.document.removeEventListener("visibilitychange", noteActivity);
    for (const eventName of ACTIVITY_EVENTS) {
      dependencies.document.removeEventListener(eventName, noteActivity);
    }
    if (intervalHandle !== null) dependencies.scheduler.clearInterval(intervalHandle);
    intervalHandle = null;
    started = false;
    return status();
  }

  async function tick() {
    if (!started || optedOut || !state) return status();
    const now = dependencies.clock.now();
    const visible = dependencies.document.visibilityState === "visible";
    const recentlyActive =
      lastActivityAt !== null && now.valueOf() - lastActivityAt.valueOf() <= IDLE_AFTER_SECONDS * 1000;
    if (visible && recentlyActive) {
      const date = reportingDateAt(now);
      rotateIfNeeded(date);
      state = recordVisit(state, { date });
      state = recordActiveReading(state, {
        sessionKey,
        seconds: TICK_SECONDS,
      });
      persist();
      await queueFlush();
    }
    return status();
  }

  async function start() {
    if (!enabled) return status();
    requireDependencies(dependencies);
    if (typeof dependencies.deliverTransition !== "function") {
      throw new TypeError("enabled adapter requires an injected delivery function");
    }
    if (dependencies.persistentStorage.getItem(OPT_OUT_KEY) === "true") {
      optedOut = true;
      eraseLocalMeasurementState();
      return status();
    }
    if (started) return status();

    const date = reportingDateAt(dependencies.clock.now());
    const month = date.slice(0, 7);
    const stored = parseState(dependencies.persistentStorage.getItem(PERSISTENT_STATE_KEY));
    state = stored || createMonthState({ month, token: dependencies.tokenFactory() });
    if (state.month !== month) {
      state = rotateMonth(state, { month, token: dependencies.tokenFactory() });
      dependencies.sessionStorage.removeItem(SESSION_KEY);
    }
    state = recordVisit(state, { date });

    sessionKey = dependencies.sessionStorage.getItem(SESSION_KEY);
    if (typeof sessionKey !== "string") {
      replaceSessionKey();
    }
    try {
      assertSessionKey(sessionKey);
    } catch {
      replaceSessionKey();
      assertSessionKey(sessionKey);
    }
    persist();

    started = true;
    optedOut = false;
    lastActivityAt = dependencies.clock.now();
    dependencies.document.addEventListener("visibilitychange", noteActivity);
    for (const eventName of ACTIVITY_EVENTS) {
      dependencies.document.addEventListener(eventName, noteActivity);
    }
    intervalHandle = dependencies.scheduler.setInterval(tick, TICK_SECONDS * 1000);
    await queueFlush();
    return status();
  }

  async function meaningfulAction(action) {
    if (!started || optedOut || !state) return status();
    const date = reportingDateAt(dependencies.clock.now());
    rotateIfNeeded(date);
    state = recordVisit(state, { date });
    state = recordMeaningfulAction(state, { sessionKey, action });
    persist();
    await queueFlush();
    return status();
  }

  function setOptOut(value) {
    if (typeof value !== "boolean") throw new TypeError("opt-out value must be boolean");
    if (!enabled) return status();
    requireDependencies(dependencies);
    if (value) {
      dependencies.persistentStorage.setItem(OPT_OUT_KEY, "true");
      optedOut = true;
      stop();
      eraseLocalMeasurementState();
    } else {
      dependencies.persistentStorage.removeItem(OPT_OUT_KEY);
      optedOut = false;
    }
    return status();
  }

  return Object.freeze({
    meaningfulAction,
    setOptOut,
    start,
    status,
    stop,
    tick,
  });
}
