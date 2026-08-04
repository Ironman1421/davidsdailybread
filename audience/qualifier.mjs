/**
 * Pure local-first qualification state machine.
 *
 * This module has no DOM, storage, analytics SDK, or network integration. A
 * future, separately approved browser adapter may persist its bounded state and
 * deliver the transition envelopes it returns.
 */

export const QUALIFIER_VERSION = 1;
export const DEFINITION_VERSION = 1;
export const MINIMUM_VISIT_DAYS = 3;
export const MINIMUM_ENGAGED_SESSIONS = 2;
export const MINIMUM_ACTIVE_READING_SECONDS = 60;

export const TRANSITIONS = Object.freeze([
  "first-seen",
  "returned",
  "qualified",
]);

export const MEANINGFUL_ACTIONS = Object.freeze([
  "archive-edition-opened",
  "library-item-opened",
  "reviewed-source-opened",
  "rss-opened",
  "local-note-used",
  "editorial-slip-submitted",
]);

const STATE_KEYS = Object.freeze([
  "activeSecondsBySession",
  "definitionVersion",
  "engagedSessionKeys",
  "month",
  "sentTransitions",
  "token",
  "version",
  "visitDates",
]);
const MONTH_PATTERN = /^[0-9]{4}-(0[1-9]|1[0-2])$/;
const DATE_PATTERN = /^[0-9]{4}-(0[1-9]|1[0-2])-[0-9]{2}$/;
const TOKEN_PATTERN = /^[A-Za-z0-9_-]{22,64}$/;
const ENVELOPE_KEYS = Object.freeze([
  "definitionVersion",
  "month",
  "token",
  "transition",
  "version",
]);

function assertExactKeys(value, expected, label) {
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (JSON.stringify(actual) !== JSON.stringify(wanted)) {
    throw new TypeError(`${label} contains unexpected or missing fields`);
  }
}

function assertMonth(month) {
  if (typeof month !== "string" || !MONTH_PATTERN.test(month)) {
    throw new TypeError("month must use YYYY-MM");
  }
}

function assertDate(date, month) {
  if (typeof date !== "string" || !DATE_PATTERN.test(date)) {
    throw new TypeError("date must use YYYY-MM-DD");
  }
  const parsed = new Date(`${date}T00:00:00Z`);
  if (Number.isNaN(parsed.valueOf()) || parsed.toISOString().slice(0, 10) !== date) {
    throw new TypeError("date must be a real calendar date");
  }
  if (!date.startsWith(`${month}-`)) {
    throw new TypeError("date must belong to the state month");
  }
}

function assertToken(token, label = "token") {
  if (typeof token !== "string" || !TOKEN_PATTERN.test(token)) {
    throw new TypeError(`${label} must be a 22 to 64 character base64url value`);
  }
}

export function assertSessionKey(sessionKey) {
  assertToken(sessionKey, "session key");
  return sessionKey;
}

function assertUniqueStrings(values, label) {
  if (!Array.isArray(values) || values.some((value) => typeof value !== "string")) {
    throw new TypeError(`${label} must be an array of strings`);
  }
  if (new Set(values).size !== values.length) {
    throw new TypeError(`${label} must not contain duplicates`);
  }
}

export function assertQualifierState(state) {
  if (!state || typeof state !== "object" || Array.isArray(state)) {
    throw new TypeError("state must be an object");
  }
  assertExactKeys(state, STATE_KEYS, "state");
  if (state.version !== QUALIFIER_VERSION) {
    throw new TypeError("unsupported qualifier state version");
  }
  if (state.definitionVersion !== DEFINITION_VERSION) {
    throw new TypeError("unsupported milestone definition version");
  }
  assertMonth(state.month);
  assertToken(state.token);

  assertUniqueStrings(state.visitDates, "visitDates");
  if (state.visitDates.length > 31 || state.visitDates.join() !== [...state.visitDates].sort().join()) {
    throw new TypeError("visitDates must be sorted and bounded to one month");
  }
  for (const date of state.visitDates) assertDate(date, state.month);

  assertUniqueStrings(state.engagedSessionKeys, "engagedSessionKeys");
  if (state.engagedSessionKeys.length > MINIMUM_ENGAGED_SESSIONS) {
    throw new TypeError("only the first two engaged session keys may be retained");
  }
  for (const sessionKey of state.engagedSessionKeys) {
    assertToken(sessionKey, "session key");
  }

  if (
    !state.activeSecondsBySession ||
    typeof state.activeSecondsBySession !== "object" ||
    Array.isArray(state.activeSecondsBySession)
  ) {
    throw new TypeError("activeSecondsBySession must be an object");
  }
  const activeEntries = Object.entries(state.activeSecondsBySession);
  if (activeEntries.length > 32) {
    throw new TypeError("active session state exceeds its local bound");
  }
  for (const [sessionKey, seconds] of activeEntries) {
    assertToken(sessionKey, "session key");
    if (!Number.isFinite(seconds) || seconds < 0 || seconds >= MINIMUM_ACTIVE_READING_SECONDS) {
      throw new TypeError("active session seconds must be finite and below the threshold");
    }
    if (state.engagedSessionKeys.includes(sessionKey)) {
      throw new TypeError("engaged sessions must not retain active-second state");
    }
  }

  assertUniqueStrings(state.sentTransitions, "sentTransitions");
  if (state.sentTransitions.some((transition) => !TRANSITIONS.includes(transition))) {
    throw new TypeError("sentTransitions contains an unknown transition");
  }
  return state;
}

export function assertTransitionEnvelope(envelope) {
  if (!envelope || typeof envelope !== "object" || Array.isArray(envelope)) {
    throw new TypeError("transition envelope must be an object");
  }
  assertExactKeys(envelope, ENVELOPE_KEYS, "transition envelope");
  if (envelope.version !== QUALIFIER_VERSION) {
    throw new TypeError("unsupported transition envelope version");
  }
  if (envelope.definitionVersion !== DEFINITION_VERSION) {
    throw new TypeError("unsupported transition definition version");
  }
  assertMonth(envelope.month);
  assertToken(envelope.token);
  if (!TRANSITIONS.includes(envelope.transition)) {
    throw new TypeError("unknown audience transition");
  }
  return envelope;
}

function cloneState(state) {
  assertQualifierState(state);
  return {
    ...state,
    activeSecondsBySession: { ...state.activeSecondsBySession },
    engagedSessionKeys: [...state.engagedSessionKeys],
    sentTransitions: [...state.sentTransitions],
    visitDates: [...state.visitDates],
  };
}

export function createMonthState({ month, token }) {
  const state = {
    version: QUALIFIER_VERSION,
    definitionVersion: DEFINITION_VERSION,
    month,
    token,
    visitDates: [],
    engagedSessionKeys: [],
    activeSecondsBySession: {},
    sentTransitions: [],
  };
  return assertQualifierState(state);
}

export function rotateMonth(_priorState, { month, token }) {
  return createMonthState({ month, token });
}

export function recordVisit(state, { date }) {
  const next = cloneState(state);
  assertDate(date, next.month);
  if (!next.visitDates.includes(date)) {
    next.visitDates.push(date);
    next.visitDates.sort();
  }
  return assertQualifierState(next);
}

export function recordActiveReading(state, { sessionKey, seconds }) {
  const next = cloneState(state);
  assertToken(sessionKey, "session key");
  if (!Number.isFinite(seconds) || seconds <= 0) {
    throw new TypeError("active reading increment must be a positive number");
  }
  if (
    next.engagedSessionKeys.includes(sessionKey) ||
    next.engagedSessionKeys.length >= MINIMUM_ENGAGED_SESSIONS
  ) {
    return next;
  }

  const total = (next.activeSecondsBySession[sessionKey] || 0) + seconds;
  if (total >= MINIMUM_ACTIVE_READING_SECONDS) {
    delete next.activeSecondsBySession[sessionKey];
    next.engagedSessionKeys.push(sessionKey);
  } else {
    if (
      !(sessionKey in next.activeSecondsBySession) &&
      Object.keys(next.activeSecondsBySession).length >= 32
    ) {
      delete next.activeSecondsBySession[Object.keys(next.activeSecondsBySession)[0]];
    }
    next.activeSecondsBySession[sessionKey] = total;
  }
  return assertQualifierState(next);
}

export function recordMeaningfulAction(state, { sessionKey, action }) {
  const next = cloneState(state);
  assertToken(sessionKey, "session key");
  if (!MEANINGFUL_ACTIONS.includes(action)) {
    throw new TypeError("meaningful action is not allowlisted");
  }
  if (
    !next.engagedSessionKeys.includes(sessionKey) &&
    next.engagedSessionKeys.length < MINIMUM_ENGAGED_SESSIONS
  ) {
    delete next.activeSecondsBySession[sessionKey];
    next.engagedSessionKeys.push(sessionKey);
  }
  return assertQualifierState(next);
}

export function eligibleTransitions(state) {
  assertQualifierState(state);
  const eligible = [];
  if (state.visitDates.length >= 1) eligible.push("first-seen");
  if (state.visitDates.length >= 2) eligible.push("returned");
  if (
    state.visitDates.length >= MINIMUM_VISIT_DAYS &&
    state.engagedSessionKeys.length >= MINIMUM_ENGAGED_SESSIONS
  ) {
    eligible.push("qualified");
  }
  return eligible;
}

export function pendingTransitions(state) {
  return eligibleTransitions(state).filter(
    (transition) => !state.sentTransitions.includes(transition),
  );
}

export function transitionEnvelope(state, transition) {
  assertQualifierState(state);
  if (!pendingTransitions(state).includes(transition)) {
    throw new TypeError("transition is not currently pending");
  }
  return assertTransitionEnvelope({
    version: QUALIFIER_VERSION,
    definitionVersion: DEFINITION_VERSION,
    month: state.month,
    transition,
    token: state.token,
  });
}

export function markTransitionSent(state, transition) {
  const next = cloneState(state);
  if (!pendingTransitions(next).includes(transition)) {
    throw new TypeError("only a pending transition may be marked sent");
  }
  next.sentTransitions.push(transition);
  return assertQualifierState(next);
}
