begin;

select plan(32);

truncate table
  reader_private.audit_events,
  reader_private.plan_items,
  reader_private.submissions,
  reader_private.plan_batches
restart identity cascade;

create temporary table reader_test_values (
  key text primary key,
  value jsonb not null
);

insert into reader_test_values values
  ('old_ask', reader_private.submit_submission(
    'ask_baker', 'old ask', 'Old Reader', 'reader-publication-v1', true, repeat('01', 32)
  )),
  ('young_ask', reader_private.submit_submission(
    'ask_baker', 'young ask', null, 'reader-publication-v1', true, repeat('02', 32)
  )),
  ('letter', reader_private.submit_submission(
    'king_letter', 'reader letter', 'Letter Writer', 'reader-publication-v1', true, repeat('03', 32)
  )),
  ('pin', reader_private.submit_submission(
    'crumb_pin', 'reader pin', null, 'reader-publication-v1', true, repeat('04', 32)
  ));

update reader_private.submissions
set submitted_at = case body
  when 'old ask' then '2026-01-01 00:00:00+00'::timestamptz
  when 'young ask' then '2026-01-02 00:00:00+00'::timestamptz
  when 'reader letter' then '2026-01-03 00:00:00+00'::timestamptz
  else '2026-01-04 00:00:00+00'::timestamptz
end;

select is(
  (select count(*)::integer from reader_private.submissions),
  4,
  'four consented submissions were created'
);

insert into reader_test_values values
  ('plan_one', reader_private.reserve_plan('2026-08-01-morning'));

select is(
  (select jsonb_array_length(value -> 'selections') from reader_test_values where key = 'plan_one'),
  3,
  'reservation selects at most one item for each kind'
);
select is(
  (
    select count(distinct selection ->> 'kind')::integer
    from reader_test_values,
      lateral jsonb_array_elements(value -> 'selections') as selection
    where key = 'plan_one'
  ),
  3,
  'reserved kinds are unique'
);
select is(
  (
    select selection ->> 'body'
    from reader_test_values,
      lateral jsonb_array_elements(value -> 'selections') as selection
    where key = 'plan_one' and selection ->> 'kind' = 'ask_baker'
  ),
  'old ask',
  'oldest ask is selected first'
);

insert into reader_test_values values
  ('plan_one_retry', reader_private.reserve_plan('2026-08-01-morning'));
select is(
  (select value ->> 'batchId' from reader_test_values where key = 'plan_one_retry'),
  (select value ->> 'batchId' from reader_test_values where key = 'plan_one'),
  'same live edition retry returns the same batch'
);
select is(
  (select (value ->> 'attempt')::integer from reader_test_values where key = 'plan_one_retry'),
  1,
  'same live edition retry keeps the attempt'
);

insert into reader_test_values values
  ('plan_two', reader_private.reserve_plan('2026-08-02-morning'));
select is(
  (select jsonb_array_length(value -> 'selections') from reader_test_values where key = 'plan_two'),
  1,
  'another edition cannot reserve rows held by a live batch'
);
select is(
  (
    select selection ->> 'body'
    from reader_test_values,
      lateral jsonb_array_elements(value -> 'selections') as selection
    where key = 'plan_two'
  ),
  'young ask',
  'the next oldest unlocked item is selected'
);

insert into reader_test_values values
  ('plan_two_release', reader_private.release_plan(
    (select (value ->> 'batchId')::uuid from reader_test_values where key = 'plan_two')
  ));
select is(
  (select value ->> 'status' from reader_test_values where key = 'plan_two_release'),
  'released',
  'release changes the batch state'
);
select is(
  (select status::text from reader_private.submissions where body = 'young ask'),
  'pending',
  'release returns an eligible item to the queue'
);

insert into reader_test_values values
  ('authorized', reader_private.authorize_publish(
    (select (value ->> 'batchId')::uuid from reader_test_values where key = 'plan_one'),
    repeat('a', 64)
  ));
select is(
  (select value ->> 'status' from reader_test_values where key = 'authorized'),
  'publishing',
  'manifest authorization enters publishing'
);
select lives_ok(
  format(
    'select reader_private.authorize_publish(%L::uuid, %L)',
    (select value ->> 'batchId' from reader_test_values where key = 'plan_one'),
    repeat('a', 64)
  ),
  'same manifest authorization is idempotent'
);
select throws_ok(
  format(
    'select reader_private.authorize_publish(%L::uuid, %L)',
    (select value ->> 'batchId' from reader_test_values where key = 'plan_one'),
    repeat('b', 64)
  ),
  '55000',
  'manifest_digest_mismatch',
  'different manifest digest is rejected'
);
select is(
  (reader_private.delete_submission(repeat('01', 32)) ->> 'outcome'),
  'public_removal_required',
  'deletion cannot cross the publishing boundary'
);
select throws_ok(
  format(
    'select reader_private.finalize_plan(%L::uuid, %L, %L, %L)',
    (select value ->> 'batchId' from reader_test_values where key = 'plan_one'),
    '2026-08-09-morning',
    repeat('c', 40),
    'remote-main:receipt-one'
  ),
  '55000',
  'batch_not_finalizable',
  'finalize requires the reserved edition'
);

insert into reader_test_values values
  ('finalized', reader_private.finalize_plan(
    (select (value ->> 'batchId')::uuid from reader_test_values where key = 'plan_one'),
    '2026-08-01-morning',
    repeat('c', 40),
    'remote-main:receipt-one'
  ));
select is(
  (select value ->> 'status' from reader_test_values where key = 'finalized'),
  'finalized',
  'valid remote receipt finalizes the batch'
);
select lives_ok(
  format(
    'select reader_private.finalize_plan(%L::uuid, %L, %L, %L)',
    (select value ->> 'batchId' from reader_test_values where key = 'plan_one'),
    '2026-08-01-morning',
    repeat('c', 40),
    'remote-main:receipt-one'
  ),
  'same-edition finalize retry is idempotent'
);
select is(
  (select count(*)::integer from reader_private.submissions where status = 'published'),
  3,
  'only selected rows become published'
);
select throws_ok(
  $$select reader_private.reserve_plan('2026-08-01-morning')$$,
  '55000',
  'edition_already_finalized',
  'a finalized edition can never reserve again'
);

update reader_private.submissions
set published_at = statement_timestamp() - interval '31 days'
where status = 'published';
select lives_ok(
  $$select reader_private.run_retention(statement_timestamp())$$,
  'retention completes'
);
select is(
  (select count(*)::integer from reader_private.submissions where status = 'published' and body is null),
  3,
  'published private payloads are erased after 30 days'
);

insert into reader_test_values values
  ('lease_one', reader_private.reserve_plan('2026-08-03-morning'));
select is(
  (select (value ->> 'attempt')::integer from reader_test_values where key = 'lease_one'),
  1,
  'first lease starts at attempt one'
);
update reader_private.plan_batches
set lease_expires_at = statement_timestamp() - interval '1 minute'
where id = (select (value ->> 'batchId')::uuid from reader_test_values where key = 'lease_one');
update reader_private.submissions
set lease_expires_at = statement_timestamp() - interval '1 minute'
where reserved_batch_id = (
  select (value ->> 'batchId')::uuid from reader_test_values where key = 'lease_one'
);
insert into reader_test_values values
  ('lease_two', reader_private.reserve_plan('2026-08-03-morning'));
select is(
  (select (value ->> 'attempt')::integer from reader_test_values where key = 'lease_two'),
  2,
  'expired lease increments the attempt monotonically'
);
select is(
  (
    select status::text
    from reader_private.plan_batches
    where id = (select (value ->> 'batchId')::uuid from reader_test_values where key = 'lease_one')
  ),
  'expired',
  'old lease is marked expired'
);
select is(
  (reader_private.delete_submission(repeat('02', 32)) ->> 'outcome'),
  'accepted',
  'reserved deletion is accepted'
);
select is(
  (
    select status::text
    from reader_private.plan_batches
    where id = (select (value ->> 'batchId')::uuid from reader_test_values where key = 'lease_two')
  ),
  'released',
  'reserved deletion invalidates the live batch'
);
select is(
  (select status::text from reader_private.submissions where id = (
    select id from reader_private.submissions where deletion_token_hash is null and deleted_at is not null limit 1
  )),
  'deleted',
  'reserved deletion erases and marks the target row'
);
select is(
  (select count(*)::integer from reader_private.audit_events where transition = 'publishing_authorized'),
  1,
  'idempotent authorization emits one audit transition'
);
select is(
  (select count(*)::integer from reader_private.audit_events where transition = 'finalized'),
  1,
  'idempotent finalization emits one audit transition'
);

insert into reader_test_values values
  ('incident_submission', reader_private.submit_submission(
    'crumb_pin', 'publishing incident', null, 'reader-publication-v1', true, repeat('05', 32)
  ));
insert into reader_test_values values
  ('incident_plan', reader_private.reserve_plan('2026-08-04-morning'));
select lives_ok(
  format(
    'select reader_private.authorize_publish(%L::uuid, %L)',
    (select value ->> 'batchId' from reader_test_values where key = 'incident_plan'),
    repeat('e', 64)
  ),
  'incident fixture enters publishing'
);
update reader_private.plan_batches
set lease_expires_at = statement_timestamp() - interval '1 minute'
where id = (select (value ->> 'batchId')::uuid from reader_test_values where key = 'incident_plan');
update reader_private.submissions
set lease_expires_at = statement_timestamp() - interval '1 minute'
where reserved_batch_id = (
  select (value ->> 'batchId')::uuid from reader_test_values where key = 'incident_plan'
);
insert into reader_test_values values
  ('incident_retry', reader_private.reserve_plan('2026-08-04-morning'));
select is(
  (select value ->> 'status' from reader_test_values where key = 'incident_retry'),
  'publishing_reconciliation_required',
  'expired publishing lease returns an incident instead of a plan'
);
select is(
  (
    select status::text
    from reader_private.plan_batches
    where id = (select (value ->> 'batchId')::uuid from reader_test_values where key = 'incident_plan')
  ),
  'publishing',
  'expired publishing batch is never released automatically'
);

select * from finish();
rollback;
