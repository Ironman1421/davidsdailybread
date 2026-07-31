import postgres from "postgres";
import type { PlanInput, SubmissionInput } from "./validation.ts";

type DatabaseResult = Record<string, unknown>;
type SqlClient = ReturnType<typeof postgres>;

let client: SqlClient | null = null;
let identityVerified = false;

function database(): SqlClient {
  if (client !== null) return client;
  const url = Deno.env.get("DDB_READER_DATABASE_URL") ?? "";
  if (!/^postgres(?:ql)?:\/\//.test(url)) {
    throw new Error("database_unconfigured");
  }
  const sslMode = Deno.env.get("DDB_READER_DATABASE_SSL_MODE") ?? "require";
  if (sslMode !== "require" && sslMode !== "disable") {
    throw new Error("database_unconfigured");
  }
  client = postgres(url, {
    max: 1,
    idle_timeout: 5,
    connect_timeout: 5,
    prepare: false,
    ssl: sslMode === "require" ? "require" : false,
  });
  return client;
}

async function verifiedDatabase(): Promise<SqlClient> {
  const sql = database();
  if (!identityVerified) {
    const rows = await sql<{ allowed: boolean }[]>`
      select
        pg_has_role(current_user, 'reader_edge', 'member')
        and not role.rolsuper
        and not role.rolbypassrls as allowed
      from pg_catalog.pg_roles as role
      where role.rolname = current_user
    `;
    if (rows.length !== 1 || rows[0].allowed !== true) {
      throw new Error("database_role_forbidden");
    }
    identityVerified = true;
  }
  return sql;
}

export async function submitSubmission(
  input: SubmissionInput,
  deletionHash: string,
): Promise<DatabaseResult> {
  const sql = await verifiedDatabase();
  const rows = await sql<{ result: DatabaseResult }[]>`
    select reader_private.submit_submission(
      ${input.kind},
      ${input.body},
      ${input.byline},
      ${input.consentVersion},
      ${input.publicationConsent},
      ${deletionHash}
    ) as result
  `;
  return rows[0].result;
}

export async function deleteSubmission(
  deletionHash: string,
): Promise<DatabaseResult> {
  const sql = await verifiedDatabase();
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const rows = await sql<{ result: DatabaseResult }[]>`
        select reader_private.delete_submission(${deletionHash}) as result
      `;
      return rows[0].result;
    } catch (error) {
      const code =
        typeof error === "object" && error !== null && "code" in error
          ? String((error as { code: unknown }).code)
          : "";
      if (code !== "40001" || attempt === 1) throw error;
    }
  }
  throw new Error("delete_retry_exhausted");
}

export async function executePlan(input: PlanInput): Promise<DatabaseResult> {
  const sql = await verifiedDatabase();
  if (input.operation === "reserve") {
    const rows = await sql<{ result: DatabaseResult }[]>`
      select reader_private.reserve_plan(${input.editionId}) as result
    `;
    return rows[0].result;
  }
  if (input.operation === "authorize-publish") {
    const rows = await sql<{ result: DatabaseResult }[]>`
      select reader_private.authorize_publish(${input.batchId}::uuid, ${input.manifestDigest}) as result
    `;
    return rows[0].result;
  }
  if (input.operation === "finalize") {
    const rows = await sql<{ result: DatabaseResult }[]>`
      select reader_private.finalize_plan(
        ${input.batchId}::uuid,
        ${input.editionId},
        ${input.commitSha},
        ${input.receipt}
      ) as result
    `;
    return rows[0].result;
  }
  if (input.operation === "release") {
    const rows = await sql<{ result: DatabaseResult }[]>`
      select reader_private.release_plan(${input.batchId}::uuid) as result
    `;
    return rows[0].result;
  }
  throw new Error("handoff_operation_requires_storage_boundary");
}

export async function authorizeHandoff(
  batchId: string,
  bundleDigest: string,
  action: "upload" | "download" | "delete",
): Promise<{ objectPath: string }> {
  const sql = await verifiedDatabase();
  const rows = await sql<{ result: { objectPath: string } }[]>`
    select reader_private.authorize_handoff(
      ${batchId}::uuid,
      ${bundleDigest},
      ${action}
    ) as result
  `;
  return rows[0].result;
}
