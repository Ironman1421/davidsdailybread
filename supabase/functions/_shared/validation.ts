import {
  CONSENT_VERSION,
  MAX_BYLINE_CHARACTERS,
  MAX_SUBMISSION_BODY_CHARACTERS,
  SUBMISSION_KINDS,
  type SubmissionKind,
} from "./constants.ts";
import { SafeHttpError } from "./errors.ts";

export interface SubmissionInput {
  kind: SubmissionKind;
  body: string;
  byline: string | null;
  consentVersion: typeof CONSENT_VERSION;
  publicationConsent: true;
  turnstileToken: string;
}

export type PlanInput =
  | { operation: "reserve"; editionId: string }
  | { operation: "authorize-publish"; batchId: string; manifestDigest: string }
  | {
    operation: "finalize";
    batchId: string;
    editionId: string;
    commitSha: string;
    receipt: string;
  }
  | { operation: "release"; batchId: string }
  | {
    operation:
      | "create-handoff-upload"
      | "create-handoff-download"
      | "delete-handoff";
    batchId: string;
    bundleDigest: string;
  }
  | { operation: "cleanup-handoffs" };

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const SHA256_PATTERN = /^[0-9a-f]{64}$/;
const COMMIT_SHA_PATTERN = /^[0-9a-f]{40}$/;
const RECEIPT_PATTERN = /^[A-Za-z0-9._:/@+~-]{1,256}$/;
const EDITION_PATTERN = /^(\d{4})-(\d{2})-(\d{2})-morning$/;
const DELETION_TOKEN_PATTERN = /^[A-Za-z0-9_-]{43}$/;

export function parseSubmissionInput(
  value: Record<string, unknown>,
): SubmissionInput {
  requireAllowedKeys(value, [
    "body",
    "consentVersion",
    "kind",
    "publicationConsent",
    "turnstileToken",
  ], ["byline"]);

  if (!SUBMISSION_KINDS.includes(value.kind as SubmissionKind)) invalid();
  const body = normalizeReaderText(
    value.body,
    MAX_SUBMISSION_BODY_CHARACTERS,
    false,
  );
  const normalizedByline = value.byline === null || value.byline === undefined
    ? ""
    : normalizeReaderText(value.byline, MAX_BYLINE_CHARACTERS, true);
  const byline = normalizedByline === "" ? null : normalizedByline;
  if (
    value.consentVersion !== CONSENT_VERSION ||
    value.publicationConsent !== true
  ) invalid();
  if (
    typeof value.turnstileToken !== "string" ||
    value.turnstileToken.length < 1 ||
    value.turnstileToken.length > 4_096
  ) invalid();

  return {
    kind: value.kind as SubmissionKind,
    body,
    byline,
    consentVersion: CONSENT_VERSION,
    publicationConsent: true,
    turnstileToken: value.turnstileToken,
  };
}

export function parseDeletionInput(value: Record<string, unknown>): string {
  requireExactKeys(value, ["deletionToken"]);
  if (
    typeof value.deletionToken !== "string" ||
    !isCanonicalDeletionToken(value.deletionToken)
  ) {
    invalid();
  }
  return value.deletionToken;
}

export function parsePlanInput(value: Record<string, unknown>): PlanInput {
  if (typeof value.operation !== "string") invalid();

  if (value.operation === "reserve") {
    requireExactKeys(value, ["editionId", "operation"]);
    if (
      typeof value.editionId !== "string" || !isMorningEdition(value.editionId)
    ) invalid();
    return { operation: "reserve", editionId: value.editionId };
  }

  if (value.operation === "authorize-publish") {
    requireExactKeys(value, ["batchId", "manifestDigest", "operation"]);
    if (
      typeof value.batchId !== "string" || !UUID_PATTERN.test(value.batchId) ||
      typeof value.manifestDigest !== "string" ||
      !SHA256_PATTERN.test(value.manifestDigest)
    ) invalid();
    return {
      operation: "authorize-publish",
      batchId: value.batchId,
      manifestDigest: value.manifestDigest,
    };
  }

  if (value.operation === "finalize") {
    requireExactKeys(value, [
      "batchId",
      "commitSha",
      "editionId",
      "operation",
      "receipt",
    ]);
    if (
      typeof value.batchId !== "string" || !UUID_PATTERN.test(value.batchId) ||
      typeof value.editionId !== "string" ||
      !isMorningEdition(value.editionId) ||
      typeof value.commitSha !== "string" ||
      !COMMIT_SHA_PATTERN.test(value.commitSha) ||
      typeof value.receipt !== "string" || !RECEIPT_PATTERN.test(value.receipt)
    ) invalid();
    return {
      operation: "finalize",
      batchId: value.batchId,
      editionId: value.editionId,
      commitSha: value.commitSha,
      receipt: value.receipt,
    };
  }

  if (value.operation === "release") {
    requireExactKeys(value, ["batchId", "operation"]);
    if (
      typeof value.batchId !== "string" || !UUID_PATTERN.test(value.batchId)
    ) invalid();
    return { operation: "release", batchId: value.batchId };
  }

  if (
    value.operation === "create-handoff-upload" ||
    value.operation === "create-handoff-download" ||
    value.operation === "delete-handoff"
  ) {
    requireExactKeys(value, ["batchId", "bundleDigest", "operation"]);
    if (
      typeof value.batchId !== "string" || !UUID_PATTERN.test(value.batchId) ||
      typeof value.bundleDigest !== "string" ||
      !SHA256_PATTERN.test(value.bundleDigest)
    ) invalid();
    return {
      operation: value.operation,
      batchId: value.batchId,
      bundleDigest: value.bundleDigest,
    };
  }

  if (value.operation === "cleanup-handoffs") {
    requireExactKeys(value, ["operation"]);
    return { operation: "cleanup-handoffs" };
  }

  invalid();
}

export function normalizeReaderText(
  value: unknown,
  maximumCharacters: number,
  optional: boolean,
): string {
  if (typeof value !== "string") invalid();
  const lineNormalized = value.replace(/\r\n?/g, "\n").replace(/\t/g, " ");
  const withoutControls = Array.from(lineNormalized).filter((character) => {
    const codePoint = character.codePointAt(0) ?? 0;
    return !(
      (codePoint >= 0 && codePoint <= 8) ||
      codePoint === 11 ||
      codePoint === 12 ||
      (codePoint >= 14 && codePoint <= 31) ||
      codePoint === 127
    );
  }).join("");
  const normalized = withoutControls.normalize("NFC").trim();
  const length = Array.from(normalized).length;
  if (length > maximumCharacters || (!optional && length < 1)) invalid();
  return normalized;
}

export function isCanonicalDeletionToken(value: string): boolean {
  if (!DELETION_TOKEN_PATTERN.test(value)) return false;
  try {
    const standard = value.replace(/-/g, "+").replace(/_/g, "/") + "=";
    const decoded = atob(standard);
    return decoded.length === 32 && encodeBase64Url(
          Uint8Array.from(decoded, (character) => character.charCodeAt(0)),
        ) === value;
  } catch {
    return false;
  }
}

export function isMorningEdition(value: string): boolean {
  const match = EDITION_PATTERN.exec(value);
  if (match === null) return false;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 &&
    date.getUTCDate() === day;
}

export function encodeBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(
    /=+$/g,
    "",
  );
}

function requireExactKeys(
  value: Record<string, unknown>,
  expectedKeys: string[],
): void {
  const actualKeys = Object.keys(value).sort();
  const expected = [...expectedKeys].sort();
  if (actualKeys.length !== expected.length) invalid();
  if (actualKeys.some((key, index) => key !== expected[index])) invalid();
}

function requireAllowedKeys(
  value: Record<string, unknown>,
  requiredKeys: string[],
  optionalKeys: string[],
): void {
  const actualKeys = Object.keys(value);
  const allowedKeys = new Set([...requiredKeys, ...optionalKeys]);
  if (requiredKeys.some((key) => !Object.hasOwn(value, key))) invalid();
  if (actualKeys.some((key) => !allowedKeys.has(key))) invalid();
}

function invalid(): never {
  throw new SafeHttpError(400, "invalid_request");
}
