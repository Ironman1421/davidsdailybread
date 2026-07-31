import assert from "node:assert/strict";
import postgres from "postgres";

const databaseUrl = process.env.DDB_READER_TEST_DATABASE_URL;
if (!databaseUrl) {
  throw new Error("DDB_READER_TEST_DATABASE_URL is required for local concurrency tests");
}

const parsedUrl = new URL(databaseUrl);
if (!["127.0.0.1", "localhost", "::1"].includes(parsedUrl.hostname)) {
  throw new Error("Concurrency tests refuse non-local database hosts");
}

const sql = postgres(databaseUrl, { max: 8, prepare: false });

async function reset() {
  await sql`
    truncate table
      reader_private.audit_events,
      reader_private.plan_items,
      reader_private.submissions,
      reader_private.plan_batches
    restart identity cascade
  `;
}

async function submit(kind, body, hashByte) {
  const hash = hashByte.repeat(32);
  const [row] = await sql`
    select reader_private.submit_submission(
      ${kind}, ${body}, null, 'reader-publication-v1', true, ${hash}
    ) as result
  `;
  return { ...row.result, hash };
}

async function reserve(editionId) {
  const [row] = await sql`select reader_private.reserve_plan(${editionId}) as result`;
  return row.result;
}

async function run() {
  await reset();
  const old = await submit("ask_baker", "locked oldest", "11");
  await submit("ask_baker", "available next", "12");
  await sql`
    update reader_private.submissions
    set submitted_at = case body
      when 'locked oldest' then '2026-01-01 00:00:00+00'::timestamptz
      else '2026-01-02 00:00:00+00'::timestamptz
    end
  `;

  let lockReady;
  let unlock;
  const ready = new Promise((resolve) => { lockReady = resolve; });
  const waitForUnlock = new Promise((resolve) => { unlock = resolve; });
  const blocker = sql.begin(async (transaction) => {
    await transaction`
      select id from reader_private.submissions
      where id = ${old.receipt}::uuid
      for update
    `;
    lockReady();
    await waitForUnlock;
  });

  await ready;
  const skippedPlan = await reserve("2026-09-01-morning");
  assert.equal(skippedPlan.selections.length, 1);
  assert.equal(skippedPlan.selections[0].body, "available next");
  unlock();
  await blocker;
  const [oldState] = await sql`
    select status::text as status from reader_private.submissions where id = ${old.receipt}::uuid
  `;
  assert.equal(oldState.status, "pending");

  await reset();
  await submit("ask_baker", "same edition", "21");
  const [sameOne, sameTwo] = await Promise.all([
    reserve("2026-09-02-morning"),
    reserve("2026-09-02-morning"),
  ]);
  assert.equal(sameOne.batchId, sameTwo.batchId);
  assert.equal(sameOne.attempt, 1);
  assert.equal(sameTwo.attempt, 1);

  await reset();
  const racing = await submit("ask_baker", "race payload", "31");
  const racePlan = await reserve("2026-09-03-morning");
  const authorization = sql`
    select reader_private.authorize_publish(${racePlan.batchId}::uuid, ${"a".repeat(64)}) as result
  `;
  const deletion = sql`
    select reader_private.delete_submission(${racing.hash}) as result
  `;
  await Promise.allSettled([authorization, deletion]);
  const [raceState] = await sql`
    select batch.status::text as batch_status, submission.status::text as submission_status
    from reader_private.plan_batches as batch
    join reader_private.submissions as submission on submission.reserved_batch_id = batch.id
    where batch.id = ${racePlan.batchId}::uuid
    union all
    select batch.status::text, submission.status::text
    from reader_private.plan_batches as batch
    join reader_private.plan_items as item on item.batch_id = batch.id
    join reader_private.submissions as submission on submission.id = item.submission_id
    where batch.id = ${racePlan.batchId}::uuid
    limit 1
  `;
  assert.ok(
    (raceState.batch_status === "publishing" && raceState.submission_status === "publishing") ||
      (raceState.batch_status === "released" && raceState.submission_status === "deleted"),
  );

  await reset();
  await submit("crumb_pin", "lease payload", "41");
  const leaseOne = await reserve("2026-09-04-morning");
  await sql`
    update reader_private.plan_batches
    set lease_expires_at = statement_timestamp() - interval '1 minute'
    where id = ${leaseOne.batchId}::uuid
  `;
  await sql`
    update reader_private.submissions
    set lease_expires_at = statement_timestamp() - interval '1 minute'
    where reserved_batch_id = ${leaseOne.batchId}::uuid
  `;
  const leaseTwo = await reserve("2026-09-04-morning");
  assert.equal(leaseTwo.attempt, 2);
  assert.notEqual(leaseOne.batchId, leaseTwo.batchId);
  const [expired] = await sql`
    select status::text as status from reader_private.plan_batches where id = ${leaseOne.batchId}::uuid
  `;
  assert.equal(expired.status, "expired");

  await reset();
  await submit("king_letter", "manifest payload", "51");
  const manifestPlan = await reserve("2026-09-05-morning");
  await sql`
    select reader_private.authorize_publish(${manifestPlan.batchId}::uuid, ${"b".repeat(64)})
  `;
  await assert.rejects(() => sql`
    select reader_private.authorize_publish(${manifestPlan.batchId}::uuid, ${"c".repeat(64)})
  `);
  const [finalizedOne] = await sql`
    select reader_private.finalize_plan(
      ${manifestPlan.batchId}::uuid,
      '2026-09-05-morning',
      ${"d".repeat(40)},
      'remote-main:concurrency-receipt'
    ) as result
  `;
  const [finalizedTwo] = await sql`
    select reader_private.finalize_plan(
      ${manifestPlan.batchId}::uuid,
      '2026-09-05-morning',
      ${"d".repeat(40)},
      'remote-main:concurrency-receipt'
    ) as result
  `;
  assert.deepEqual(finalizedOne.result, finalizedTwo.result);

  console.log("reader concurrency and locking checks passed");
}

try {
  await run();
} finally {
  await sql.end({ timeout: 1 });
}
