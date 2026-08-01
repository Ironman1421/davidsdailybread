import assert from "node:assert/strict";
import test from "node:test";

import {
  constantTimeTextEqual,
  newDeletionToken,
  sha256Hex,
} from "../_shared/crypto.ts";
import { SafeHttpError } from "../_shared/errors.ts";
import {
  browserOrigin,
  handleBrowserPreflight,
  readBrowserJson,
  requireBrokerPost,
} from "../_shared/http.ts";
import {
  isCanonicalDeletionToken,
  normalizeReaderText,
  parseDeletionInput,
  parsePlanInput,
  parseSubmissionInput,
} from "../_shared/validation.ts";

const origin = "https://davidsdailybread.com";

test("reader text normalization and Unicode code-point limits are deterministic", () => {
  assert.equal(
    normalizeReaderText("  cafe\u0301\r\nnext\tline\u0000  ", 20, false),
    "café\nnext line",
  );
  assert.equal(normalizeReaderText("😀😀", 2, false), "😀😀");
  assert.throws(() => normalizeReaderText("😀😀", 1, false), SafeHttpError);
  assert.throws(
    () => normalizeReaderText("\u0000\t", 10, false),
    SafeHttpError,
  );
});

test("submission input is exact, consented, normalized, and bounded", () => {
  const parsed = parseSubmissionInput({
    kind: "ask_baker",
    body: " Question?\r\n",
    byline: " Reader ",
    consentVersion: "reader-publication-v1",
    publicationConsent: true,
    turnstileToken: "turnstile-response",
  });
  assert.deepEqual(parsed, {
    kind: "ask_baker",
    body: "Question?",
    byline: "Reader",
    consentVersion: "reader-publication-v1",
    publicationConsent: true,
    turnstileToken: "turnstile-response",
  });
  assert.throws(
    () => parseSubmissionInput({ ...parsed, unexpected: true }),
    SafeHttpError,
  );
  assert.throws(
    () => parseSubmissionInput({ ...parsed, publicationConsent: false }),
    SafeHttpError,
  );
  assert.throws(
    () => parseSubmissionInput({ ...parsed, body: "x".repeat(2_001) }),
    SafeHttpError,
  );
  const anonymous = parseSubmissionInput({
    kind: "crumb_pin",
    body: "Anonymous pin",
    consentVersion: "reader-publication-v1",
    publicationConsent: true,
    turnstileToken: "turnstile-response",
  });
  assert.equal(anonymous.byline, null);
});

test("deletion tokens are 256-bit canonical base64url values and hash consistently", async () => {
  const token = newDeletionToken();
  assert.equal(token.length, 43);
  assert.equal(isCanonicalDeletionToken(token), true);
  assert.equal(parseDeletionInput({ deletionToken: token }), token);
  assert.match(await sha256Hex(token), /^[0-9a-f]{64}$/);
  assert.throws(
    () => parseDeletionInput({ deletionToken: token + "A" }),
    SafeHttpError,
  );
});

test("broker tokens use a full constant-time comparison loop", () => {
  assert.equal(constantTimeTextEqual("same", "same"), true);
  assert.equal(constantTimeTextEqual("same", "sand"), false);
  assert.equal(constantTimeTextEqual("short", "longer"), false);
});

test("browser origin and preflight checks are exact", () => {
  assert.equal(
    browserOrigin(
      new Request("https://local.test", { headers: { Origin: origin } }),
    ),
    origin,
  );
  assert.throws(
    () =>
      browserOrigin(
        new Request("https://local.test", {
          headers: { Origin: `${origin}.evil` },
        }),
      ),
    SafeHttpError,
  );

  const response = handleBrowserPreflight(
    new Request("https://local.test", {
      method: "OPTIONS",
      headers: {
        Origin: origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
      },
    }),
  );
  assert.equal(response?.status, 204);
  assert.equal(response?.headers.get("Access-Control-Allow-Origin"), origin);
  assert.equal(
    response?.headers.get("Access-Control-Allow-Methods"),
    "POST, OPTIONS",
  );
});

test("JSON requests require an exact content type and bounded plain object", async () => {
  const good = new Request("https://local.test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value: 1 }),
  });
  assert.deepEqual(await readBrowserJson(good), { value: 1 });

  const charset = new Request("https://local.test", {
    method: "POST",
    headers: { "Content-Type": "application/json; charset=utf-8" },
    body: "{}",
  });
  await assert.rejects(() => readBrowserJson(charset), SafeHttpError);

  const oversized = new Request("https://local.test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value: "x".repeat(12_288) }),
  });
  await assert.rejects(() => readBrowserJson(oversized), SafeHttpError);
});

test("broker rejects browser-originated requests", () => {
  assert.throws(
    () =>
      requireBrokerPost(
        new Request("https://local.test", {
          method: "POST",
          headers: { Origin: origin },
        }),
      ),
    SafeHttpError,
  );
});

test("plan validation accepts only bounded morning operations", () => {
  assert.deepEqual(
    parsePlanInput({ operation: "reserve", editionId: "2026-07-31-morning" }),
    {
      operation: "reserve",
      editionId: "2026-07-31-morning",
    },
  );
  assert.throws(
    () =>
      parsePlanInput({ operation: "reserve", editionId: "2026-02-30-morning" }),
    SafeHttpError,
  );
  assert.deepEqual(
    parsePlanInput({
      operation: "authorize-publish",
      batchId: "019fb9f2-8499-7691-b4c1-6568291f2df3",
      manifestDigest: "a".repeat(64),
    }),
    {
      operation: "authorize-publish",
      batchId: "019fb9f2-8499-7691-b4c1-6568291f2df3",
      manifestDigest: "a".repeat(64),
    },
  );
  assert.throws(() =>
    parsePlanInput({
      operation: "finalize",
      batchId: "019fb9f2-8499-7691-b4c1-6568291f2df3",
      editionId: "2026-07-31-morning",
      commitSha: "A".repeat(40),
      receipt: "remote-main:bad",
    }), SafeHttpError);
  assert.deepEqual(
    parsePlanInput({
      operation: "create-handoff-upload",
      batchId: "019fb9f2-8499-7691-b4c1-6568291f2df3",
      bundleDigest: "f".repeat(64),
    }),
    {
      operation: "create-handoff-upload",
      batchId: "019fb9f2-8499-7691-b4c1-6568291f2df3",
      bundleDigest: "f".repeat(64),
    },
  );
  assert.deepEqual(parsePlanInput({ operation: "cleanup-handoffs" }), {
    operation: "cleanup-handoffs",
  });
  assert.throws(
    () => parsePlanInput({ operation: "cleanup-handoffs", bucket: "other" }),
    SafeHttpError,
  );
});
