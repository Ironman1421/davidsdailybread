import assert from "node:assert/strict";
import test from "node:test";

import { databaseTls } from "../_shared/database.ts";

const ca = [
  "-----BEGIN CERTIFICATE-----",
  "c3ludGhldGljLXRlc3QtY2VydGlmaWNhdGU=",
  "-----END CERTIFICATE-----",
].join("\n");

test("remote database TLS verifies both the CA and hostname", () => {
  assert.deepEqual(
    databaseTls(
      "postgresql://reader:secret@aws-0-us-west-1.pooler.supabase.com:6543/postgres",
      "verify-full",
      ca,
    ),
    { ca, rejectUnauthorized: true },
  );
});

test("remote database URLs cannot disable TLS", () => {
  for (
    const hostname of [
      "db.example.com",
      "localhost.example.com",
      "192.0.2.10",
    ]
  ) {
    assert.throws(
      () =>
        databaseTls(
          `postgresql://reader:secret@${hostname}:5432/postgres`,
          "disable",
          "",
        ),
      /database_unconfigured/,
    );
  }
});

test("only loopback development URLs may explicitly disable TLS", () => {
  for (
    const url of [
      "postgresql://postgres:postgres@localhost:54322/postgres",
      "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
      "postgresql://postgres:postgres@[::1]:54322/postgres",
    ]
  ) {
    assert.equal(databaseTls(url, "disable", ""), false);
  }
});

test("remote verification fails closed without a PEM CA certificate", () => {
  const url = "postgresql://reader:secret@db.example.com:5432/postgres";
  for (const invalidCa of ["", "not-a-certificate"]) {
    assert.throws(
      () => databaseTls(url, "verify-full", invalidCa),
      /database_unconfigured/,
    );
  }
  assert.throws(
    () => databaseTls(url, "require", ca),
    /database_unconfigured/,
  );
});
