-- David's Daily Bread private reader-store foundation.
-- Generated with `supabase migration new reader_private_foundation` using CLI 2.111.0.

create extension if not exists pgcrypto with schema extensions;
create extension if not exists pg_cron with schema pg_catalog;

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'reader_edge') then
    create role reader_edge
      nologin
      nosuperuser
      nocreatedb
      nocreaterole
      noreplication
      nobypassrls;
  end if;
end
$$;

create schema reader_private;

revoke all on schema reader_private from public, anon, authenticated, service_role;
grant usage on schema reader_private to reader_edge;

alter default privileges for role postgres in schema reader_private
  revoke all on tables from public, anon, authenticated, service_role;
alter default privileges for role postgres in schema reader_private
  revoke all on sequences from public, anon, authenticated, service_role;
alter default privileges for role postgres in schema reader_private
  revoke execute on functions from public, anon, authenticated, service_role;

create type reader_private.submission_kind as enum (
  'ask_baker',
  'king_letter',
  'crumb_pin'
);

create type reader_private.submission_status as enum (
  'pending',
  'reserved',
  'publishing',
  'published',
  'rejected',
  'deleted',
  'expired'
);

create type reader_private.plan_batch_status as enum (
  'reserved',
  'publishing',
  'finalized',
  'released',
  'expired'
);

create table reader_private.submissions (
  id uuid primary key default extensions.gen_random_uuid(),
  kind reader_private.submission_kind not null,
  body text,
  byline text,
  submitted_at timestamptz not null default statement_timestamp(),
  consent_version text not null,
  publication_consent boolean not null,
  status reader_private.submission_status not null default 'pending',
  deletion_token_hash bytea,
  reserved_batch_id uuid,
  reserved_at timestamptz,
  lease_expires_at timestamptz,
  published_edition_id text,
  published_commit_sha text,
  published_at timestamptz,
  rejection_code text,
  deleted_at timestamptz,
  payload_erased_at timestamptz,
  constraint submissions_body_length_check check (
    body is null or char_length(body) between 1 and 2000
  ),
  constraint submissions_byline_length_check check (
    byline is null or char_length(byline) between 1 and 60
  ),
  constraint submissions_consent_check check (
    publication_consent is true
    and consent_version = 'reader-publication-v1'
  ),
  constraint submissions_deletion_hash_check check (
    deletion_token_hash is null or octet_length(deletion_token_hash) = 32
  ),
  constraint submissions_payload_erasure_check check (
    (body is null) = (payload_erased_at is not null)
  ),
  constraint submissions_publication_sha_check check (
    published_commit_sha is null
    or published_commit_sha ~ '^[0-9a-f]{40}$'
  ),
  constraint submissions_publication_fields_check check (
    (published_edition_id is null and published_commit_sha is null and published_at is null)
    or
    (published_edition_id is not null and published_commit_sha is not null and published_at is not null)
  ),
  constraint submissions_reservation_fields_check check (
    (
      status in ('reserved', 'publishing', 'published')
      and reserved_batch_id is not null
      and reserved_at is not null
      and lease_expires_at is not null
    )
    or
    (
      status not in ('reserved', 'publishing', 'published')
      and reserved_batch_id is null
      and reserved_at is null
      and lease_expires_at is null
    )
  ),
  constraint submissions_active_payload_check check (
    status not in ('pending', 'reserved', 'publishing')
    or (body is not null and deletion_token_hash is not null)
  ),
  constraint submissions_terminal_fields_check check (
    (
      status = 'published'
      and published_edition_id is not null
      and rejection_code is null
      and deleted_at is null
    )
    or
    (
      status = 'rejected'
      and rejection_code is not null
      and published_edition_id is null
      and deleted_at is null
    )
    or
    (
      status = 'deleted'
      and deleted_at is not null
      and payload_erased_at is not null
      and published_edition_id is null
      and rejection_code is null
      and deletion_token_hash is null
    )
    or
    (
      status = 'expired'
      and payload_erased_at is not null
      and published_edition_id is null
      and rejection_code is null
      and deleted_at is null
      and deletion_token_hash is null
    )
    or
    (
      status in ('pending', 'reserved', 'publishing')
      and published_edition_id is null
      and rejection_code is null
      and deleted_at is null
      and payload_erased_at is null
    )
  )
);

create table reader_private.plan_batches (
  id uuid primary key default extensions.gen_random_uuid(),
  edition_id text not null,
  attempt integer not null,
  slot text not null default 'morning',
  status reader_private.plan_batch_status not null default 'reserved',
  created_at timestamptz not null default statement_timestamp(),
  lease_expires_at timestamptz not null,
  authorized_manifest_digest text,
  authorized_at timestamptz,
  published_commit_sha text,
  verification_receipt text,
  finalized_at timestamptz,
  released_at timestamptz,
  expired_at timestamptz,
  incident_at timestamptz,
  invalidation_code text,
  constraint plan_batches_edition_check check (
    edition_id ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}-morning$'
  ),
  constraint plan_batches_attempt_check check (attempt > 0),
  constraint plan_batches_slot_check check (slot = 'morning'),
  constraint plan_batches_manifest_check check (
    authorized_manifest_digest is null
    or authorized_manifest_digest ~ '^[0-9a-f]{64}$'
  ),
  constraint plan_batches_commit_check check (
    published_commit_sha is null
    or published_commit_sha ~ '^[0-9a-f]{40}$'
  ),
  constraint plan_batches_receipt_check check (
    verification_receipt is null
    or (
      char_length(verification_receipt) between 1 and 256
      and verification_receipt ~ '^[A-Za-z0-9._:/@+~-]+$'
    )
  ),
  constraint plan_batches_invalidation_check check (
    invalidation_code is null
    or (
      char_length(invalidation_code) between 1 and 80
      and invalidation_code ~ '^[a-z0-9_-]+$'
    )
  ),
  constraint plan_batches_state_fields_check check (
    (
      status = 'reserved'
      and authorized_manifest_digest is null
      and authorized_at is null
      and published_commit_sha is null
      and finalized_at is null
      and released_at is null
      and expired_at is null
    )
    or
    (
      status = 'publishing'
      and authorized_manifest_digest is not null
      and authorized_at is not null
      and published_commit_sha is null
      and finalized_at is null
      and released_at is null
      and expired_at is null
    )
    or
    (
      status = 'finalized'
      and authorized_manifest_digest is not null
      and authorized_at is not null
      and published_commit_sha is not null
      and verification_receipt is not null
      and finalized_at is not null
      and released_at is null
      and expired_at is null
    )
    or
    (
      status = 'released'
      and published_commit_sha is null
      and finalized_at is null
      and released_at is not null
      and expired_at is null
    )
    or
    (
      status = 'expired'
      and published_commit_sha is null
      and finalized_at is null
      and released_at is null
      and expired_at is not null
    )
  ),
  unique (edition_id, attempt)
);

alter table reader_private.submissions
  add constraint submissions_reserved_batch_fkey
  foreign key (reserved_batch_id)
  references reader_private.plan_batches(id)
  on delete restrict;

create table reader_private.plan_items (
  id uuid primary key default extensions.gen_random_uuid(),
  batch_id uuid not null references reader_private.plan_batches(id) on delete cascade,
  submission_id uuid not null references reader_private.submissions(id) on delete cascade,
  kind reader_private.submission_kind not null,
  selection_digest text not null,
  selected_at timestamptz not null default statement_timestamp(),
  active boolean not null default true,
  invalidated_at timestamptz,
  published_edition_id text,
  published_commit_sha text,
  constraint plan_items_selection_digest_check check (
    selection_digest ~ '^[0-9a-f]{64}$'
  ),
  constraint plan_items_active_check check (
    (active and invalidated_at is null and published_edition_id is null and published_commit_sha is null)
    or
    (not active)
  ),
  constraint plan_items_publication_check check (
    (published_edition_id is null and published_commit_sha is null)
    or
    (published_edition_id is not null and published_commit_sha ~ '^[0-9a-f]{40}$')
  ),
  unique (batch_id, kind),
  unique (batch_id, submission_id)
);

create table reader_private.audit_events (
  id bigint generated always as identity primary key,
  object_type text not null check (object_type in ('submission', 'plan_batch', 'retention')),
  object_id uuid,
  transition text not null check (
    char_length(transition) between 1 and 80
    and transition ~ '^[a-z0-9_-]+$'
  ),
  occurred_at timestamptz not null default statement_timestamp(),
  actor text not null check (
    actor in ('reader-submit', 'reader-delete', 'reader-plan', 'reader-retention')
  )
);

create unique index plan_batches_one_live_or_finalized_edition_idx
  on reader_private.plan_batches (edition_id)
  where status in ('reserved', 'publishing', 'finalized');

create index plan_batches_lease_idx
  on reader_private.plan_batches (lease_expires_at, id)
  where status in ('reserved', 'publishing');

create index submissions_kind_status_submitted_idx
  on reader_private.submissions (kind, status, submitted_at, id);

create index submissions_reserved_batch_idx
  on reader_private.submissions (reserved_batch_id)
  where reserved_batch_id is not null;

create unique index submissions_deletion_token_hash_idx
  on reader_private.submissions (deletion_token_hash)
  where deletion_token_hash is not null;

create index submissions_retention_idx
  on reader_private.submissions (status, submitted_at, published_at);

create index plan_items_batch_idx
  on reader_private.plan_items (batch_id, submission_id);

create unique index plan_items_one_active_batch_per_submission_idx
  on reader_private.plan_items (submission_id)
  where active;

create index audit_events_occurred_idx
  on reader_private.audit_events (occurred_at, id);

alter table reader_private.submissions enable row level security;
alter table reader_private.submissions force row level security;
alter table reader_private.plan_batches enable row level security;
alter table reader_private.plan_batches force row level security;
alter table reader_private.plan_items enable row level security;
alter table reader_private.plan_items force row level security;
alter table reader_private.audit_events enable row level security;
alter table reader_private.audit_events force row level security;

create function reader_private.constant_time_equal(left_value bytea, right_value bytea)
returns boolean
language plpgsql
immutable
strict
set search_path = ''
as $$
declare
  difference integer := 0;
  offset_index integer;
begin
  if octet_length(left_value) <> octet_length(right_value) then
    return false;
  end if;

  for offset_index in 0 .. octet_length(left_value) - 1 loop
    difference := difference | (
      get_byte(left_value, offset_index) # get_byte(right_value, offset_index)
    );
  end loop;

  return difference = 0;
end
$$;

create function reader_private.write_audit(
  event_object_type text,
  event_object_id uuid,
  event_transition text,
  event_actor text
)
returns void
language sql
volatile
set search_path = ''
as $$
  insert into reader_private.audit_events (
    object_type,
    object_id,
    transition,
    actor
  ) values (
    event_object_type,
    event_object_id,
    event_transition,
    event_actor
  );
$$;

create function reader_private.plan_response(target_batch_id uuid)
returns jsonb
language sql
stable
set search_path = ''
as $$
  select jsonb_build_object(
    'batchId', batch.id,
    'editionId', batch.edition_id,
    'attempt', batch.attempt,
    'status', batch.status,
    'leaseExpiresAt', batch.lease_expires_at,
    'selections', coalesce(
      jsonb_agg(
        jsonb_build_object(
          'selectionReference', item.id,
          'kind', item.kind,
          'body', submission.body,
          'byline', submission.byline
        ) order by item.kind::text
      ) filter (where item.id is not null),
      '[]'::jsonb
    )
  )
  from reader_private.plan_batches as batch
  left join reader_private.plan_items as item
    on item.batch_id = batch.id and item.active
  left join reader_private.submissions as submission
    on submission.id = item.submission_id
  where batch.id = target_batch_id
  group by batch.id;
$$;

create function reader_private.reclaim_expired_leases(reference_time timestamptz)
returns void
language plpgsql
volatile
set search_path = ''
as $$
declare
  candidate_batch_id uuid;
  candidate_submission_id uuid;
  locked_batch reader_private.plan_batches%rowtype;
begin
  loop
    select submission.id, submission.reserved_batch_id
      into candidate_submission_id, candidate_batch_id
    from reader_private.submissions as submission
    where submission.status = 'reserved'
      and submission.lease_expires_at <= reference_time
      and submission.id = (
        select batch_submission.id
        from reader_private.submissions as batch_submission
        where batch_submission.reserved_batch_id = submission.reserved_batch_id
          and batch_submission.status = 'reserved'
        order by batch_submission.id
        limit 1
      )
    order by submission.lease_expires_at, submission.id
    for update skip locked
    limit 1;

    exit when candidate_submission_id is null;

    perform 1
    from reader_private.submissions as submission
    where submission.reserved_batch_id = candidate_batch_id
    order by submission.id
    for update;

    select * into locked_batch
    from reader_private.plan_batches as batch
    where batch.id = candidate_batch_id
    for update;

    if locked_batch.status = 'reserved'
       and locked_batch.lease_expires_at <= reference_time then
      update reader_private.submissions
      set status = 'pending',
          reserved_batch_id = null,
          reserved_at = null,
          lease_expires_at = null
      where reserved_batch_id = candidate_batch_id
        and status = 'reserved';

      update reader_private.plan_items
      set active = false,
          invalidated_at = reference_time
      where batch_id = candidate_batch_id
        and active;

      update reader_private.plan_batches
      set status = 'expired',
          expired_at = reference_time,
          invalidation_code = 'lease_expired'
      where id = candidate_batch_id;

      perform reader_private.write_audit(
        'plan_batch', candidate_batch_id, 'expired', 'reader-plan'
      );
    else
      raise exception using errcode = '55000', message = 'lease_state_inconsistent';
    end if;

    candidate_submission_id := null;
    candidate_batch_id := null;
  end loop;

  loop
    select submission.id, submission.reserved_batch_id
      into candidate_submission_id, candidate_batch_id
    from reader_private.submissions as submission
    join reader_private.plan_batches as batch
      on batch.id = submission.reserved_batch_id
    where submission.status = 'publishing'
      and batch.status = 'publishing'
      and batch.lease_expires_at <= reference_time
      and batch.incident_at is null
      and submission.id = (
        select batch_submission.id
        from reader_private.submissions as batch_submission
        where batch_submission.reserved_batch_id = submission.reserved_batch_id
          and batch_submission.status = 'publishing'
        order by batch_submission.id
        limit 1
      )
    order by batch.lease_expires_at, submission.id
    for update of submission skip locked
    limit 1;

    exit when candidate_submission_id is null;

    perform 1
    from reader_private.submissions as submission
    where submission.reserved_batch_id = candidate_batch_id
    order by submission.id
    for update;

    select * into locked_batch
    from reader_private.plan_batches as batch
    where batch.id = candidate_batch_id
    for update;

    if locked_batch.status = 'publishing'
       and locked_batch.lease_expires_at <= reference_time
       and locked_batch.incident_at is null then
      update reader_private.plan_batches
      set incident_at = reference_time
      where id = candidate_batch_id;

      perform reader_private.write_audit(
        'plan_batch', candidate_batch_id, 'publishing_lease_incident', 'reader-plan'
      );
    end if;

    candidate_submission_id := null;
    candidate_batch_id := null;
  end loop;
end
$$;

create function reader_private.submit_submission(
  requested_kind text,
  normalized_body text,
  normalized_byline text,
  requested_consent_version text,
  requested_publication_consent boolean,
  deletion_hash_hex text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  created_submission reader_private.submissions%rowtype;
begin
  if requested_kind not in ('ask_baker', 'king_letter', 'crumb_pin') then
    raise exception using errcode = '22023', message = 'invalid_submission';
  end if;
  if normalized_body is null or char_length(normalized_body) not between 1 and 2000 then
    raise exception using errcode = '22023', message = 'invalid_submission';
  end if;
  if normalized_byline is not null and char_length(normalized_byline) not between 1 and 60 then
    raise exception using errcode = '22023', message = 'invalid_submission';
  end if;
  if requested_consent_version <> 'reader-publication-v1'
     or requested_publication_consent is not true then
    raise exception using errcode = '22023', message = 'invalid_submission';
  end if;
  if deletion_hash_hex is null or deletion_hash_hex !~ '^[0-9a-f]{64}$' then
    raise exception using errcode = '22023', message = 'invalid_submission';
  end if;

  insert into reader_private.submissions (
    kind,
    body,
    byline,
    consent_version,
    publication_consent,
    deletion_token_hash
  ) values (
    requested_kind::reader_private.submission_kind,
    normalized_body,
    nullif(normalized_byline, ''),
    requested_consent_version,
    requested_publication_consent,
    decode(deletion_hash_hex, 'hex')
  )
  returning * into created_submission;

  perform reader_private.write_audit(
    'submission', created_submission.id, 'submitted', 'reader-submit'
  );

  return jsonb_build_object(
    'receipt', created_submission.id,
    'submittedAt', created_submission.submitted_at
  );
end
$$;

create function reader_private.reserve_plan(requested_edition_id text)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  reference_time timestamptz := statement_timestamp();
  selected_batch reader_private.plan_batches%rowtype;
  selected_submission reader_private.submissions%rowtype;
  next_attempt integer;
  requested_kind reader_private.submission_kind;
begin
  if requested_edition_id is null
     or requested_edition_id !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}-morning$' then
    raise exception using errcode = '22023', message = 'invalid_edition';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(requested_edition_id, 724177)
  );

  perform reader_private.reclaim_expired_leases(reference_time);

  select * into selected_batch
  from reader_private.plan_batches as batch
  where batch.edition_id = requested_edition_id
    and batch.status in ('reserved', 'publishing')
  order by batch.attempt desc
  limit 1;

  if selected_batch.id is not null then
    perform 1
    from reader_private.submissions as submission
    where submission.reserved_batch_id = selected_batch.id
    order by submission.id
    for update;

    select * into selected_batch
    from reader_private.plan_batches as batch
    where batch.id = selected_batch.id
    for update;

    if selected_batch.status = 'publishing'
       and selected_batch.lease_expires_at <= reference_time then
      if selected_batch.incident_at is null then
        update reader_private.plan_batches
        set incident_at = reference_time
        where id = selected_batch.id;

        perform reader_private.write_audit(
          'plan_batch', selected_batch.id, 'publishing_lease_incident', 'reader-plan'
        );
      end if;

      return jsonb_build_object(
        'batchId', selected_batch.id,
        'editionId', selected_batch.edition_id,
        'attempt', selected_batch.attempt,
        'status', 'publishing_reconciliation_required',
        'incidentAt', coalesce(selected_batch.incident_at, reference_time),
        'selections', '[]'::jsonb
      );
    end if;

    if selected_batch.status = 'reserved'
       and selected_batch.lease_expires_at <= reference_time then
      update reader_private.plan_batches
      set status = 'expired',
          expired_at = reference_time,
          invalidation_code = 'lease_expired'
      where id = selected_batch.id;

      perform reader_private.write_audit(
        'plan_batch', selected_batch.id, 'expired', 'reader-plan'
      );

      selected_batch := null;
    end if;

    if selected_batch.id is not null
       and selected_batch.status in ('reserved', 'publishing') then
      return reader_private.plan_response(selected_batch.id);
    end if;
  end if;

  if exists (
    select 1
    from reader_private.plan_batches as batch
    where batch.edition_id = requested_edition_id
      and batch.status = 'finalized'
  ) then
    raise exception using errcode = '55000', message = 'edition_already_finalized';
  end if;

  select coalesce(max(batch.attempt), 0) + 1
    into next_attempt
  from reader_private.plan_batches as batch
  where batch.edition_id = requested_edition_id;

  insert into reader_private.plan_batches (
    edition_id,
    attempt,
    lease_expires_at
  ) values (
    requested_edition_id,
    next_attempt,
    reference_time + interval '120 minutes'
  )
  returning * into selected_batch;

  foreach requested_kind in array enum_range(null::reader_private.submission_kind) loop
    selected_submission := null;

    select submission.* into selected_submission
    from reader_private.submissions as submission
    where submission.kind = requested_kind
      and submission.status = 'pending'
    order by submission.submitted_at, submission.id
    for update skip locked
    limit 1;

    if selected_submission.id is not null then
      update reader_private.submissions
      set status = 'reserved',
          reserved_batch_id = selected_batch.id,
          reserved_at = reference_time,
          lease_expires_at = selected_batch.lease_expires_at
      where id = selected_submission.id;

      insert into reader_private.plan_items (
        batch_id,
        submission_id,
        kind,
        selection_digest
      ) values (
        selected_batch.id,
        selected_submission.id,
        selected_submission.kind,
        encode(
          extensions.digest(
            jsonb_build_array(
              selected_submission.id,
              selected_submission.kind,
              selected_submission.body,
              selected_submission.byline
            )::text,
            'sha256'
          ),
          'hex'
        )
      );
    end if;
  end loop;

  perform reader_private.write_audit(
    'plan_batch', selected_batch.id, 'reserved', 'reader-plan'
  );

  return reader_private.plan_response(selected_batch.id);
end
$$;

create function reader_private.authorize_publish(
  requested_batch_id uuid,
  requested_manifest_digest text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  reference_time timestamptz := statement_timestamp();
  selected_batch reader_private.plan_batches%rowtype;
  invalid_selection_count integer;
begin
  if requested_manifest_digest is null
     or requested_manifest_digest !~ '^[0-9a-f]{64}$' then
    raise exception using errcode = '22023', message = 'invalid_manifest_digest';
  end if;

  perform 1
  from reader_private.submissions as submission
  join reader_private.plan_items as item
    on item.submission_id = submission.id
  where item.batch_id = requested_batch_id
    and item.active
  order by submission.id
  for update of submission;

  select * into selected_batch
  from reader_private.plan_batches as batch
  where batch.id = requested_batch_id
  for update;

  if selected_batch.id is null then
    raise exception using errcode = '22023', message = 'unknown_batch';
  end if;

  if selected_batch.status = 'publishing' then
    if selected_batch.authorized_manifest_digest = requested_manifest_digest then
      return jsonb_build_object(
        'batchId', selected_batch.id,
        'status', selected_batch.status,
        'manifestDigest', selected_batch.authorized_manifest_digest
      );
    end if;
    raise exception using errcode = '55000', message = 'manifest_digest_mismatch';
  end if;

  if selected_batch.status <> 'reserved'
     or selected_batch.lease_expires_at <= reference_time then
    raise exception using errcode = '55000', message = 'batch_not_authorizable';
  end if;

  select count(*) into invalid_selection_count
  from reader_private.plan_items as item
  join reader_private.submissions as submission
    on submission.id = item.submission_id
  where item.batch_id = requested_batch_id
    and (
      not item.active
      or submission.status <> 'reserved'
      or submission.reserved_batch_id <> requested_batch_id
      or submission.lease_expires_at <= reference_time
      or submission.publication_consent is not true
      or submission.consent_version <> 'reader-publication-v1'
      or submission.body is null
      or submission.deleted_at is not null
      or item.kind <> submission.kind
      or item.selection_digest <> encode(
        extensions.digest(
          jsonb_build_array(
            submission.id,
            submission.kind,
            submission.body,
            submission.byline
          )::text,
          'sha256'
        ),
        'hex'
      )
    );

  if invalid_selection_count <> 0 then
    raise exception using errcode = '55000', message = 'selection_invalidated';
  end if;

  update reader_private.plan_batches
  set status = 'publishing',
      authorized_manifest_digest = requested_manifest_digest,
      authorized_at = reference_time
  where id = requested_batch_id;

  update reader_private.submissions
  set status = 'publishing'
  where reserved_batch_id = requested_batch_id
    and status = 'reserved';

  perform reader_private.write_audit(
    'plan_batch', requested_batch_id, 'publishing_authorized', 'reader-plan'
  );

  return jsonb_build_object(
    'batchId', requested_batch_id,
    'status', 'publishing',
    'manifestDigest', requested_manifest_digest
  );
end
$$;

create function reader_private.finalize_plan(
  requested_batch_id uuid,
  requested_edition_id text,
  requested_commit_sha text,
  requested_verification_receipt text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  reference_time timestamptz := statement_timestamp();
  selected_batch reader_private.plan_batches%rowtype;
begin
  if requested_edition_id is null
     or requested_edition_id !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}-morning$'
     or requested_commit_sha is null
     or requested_commit_sha !~ '^[0-9a-f]{40}$'
     or requested_verification_receipt is null
     or char_length(requested_verification_receipt) not between 1 and 256
     or requested_verification_receipt !~ '^[A-Za-z0-9._:/@+~-]+$' then
    raise exception using errcode = '22023', message = 'invalid_finalization';
  end if;

  perform 1
  from reader_private.submissions as submission
  join reader_private.plan_items as item
    on item.submission_id = submission.id
  where item.batch_id = requested_batch_id
    and item.active
  order by submission.id
  for update of submission;

  select * into selected_batch
  from reader_private.plan_batches as batch
  where batch.id = requested_batch_id
  for update;

  if selected_batch.id is null then
    raise exception using errcode = '22023', message = 'unknown_batch';
  end if;

  if selected_batch.status = 'finalized' then
    if selected_batch.edition_id = requested_edition_id
       and selected_batch.published_commit_sha = requested_commit_sha
       and selected_batch.verification_receipt = requested_verification_receipt then
      return jsonb_build_object(
        'batchId', selected_batch.id,
        'status', selected_batch.status,
        'commitSha', selected_batch.published_commit_sha
      );
    end if;
    raise exception using errcode = '55000', message = 'finalization_mismatch';
  end if;

  if selected_batch.status <> 'publishing'
     or selected_batch.edition_id <> requested_edition_id then
    raise exception using errcode = '55000', message = 'batch_not_finalizable';
  end if;

  if exists (
    select 1
    from reader_private.submissions as submission
    join reader_private.plan_items as item
      on item.submission_id = submission.id
    where item.batch_id = requested_batch_id
      and (
        not item.active
        or submission.status <> 'publishing'
        or submission.reserved_batch_id <> requested_batch_id
      )
  ) then
    raise exception using errcode = '55000', message = 'selection_invalidated';
  end if;

  update reader_private.plan_batches
  set status = 'finalized',
      published_commit_sha = requested_commit_sha,
      verification_receipt = requested_verification_receipt,
      finalized_at = reference_time
  where id = requested_batch_id;

  update reader_private.submissions
  set status = 'published',
      published_edition_id = requested_edition_id,
      published_commit_sha = requested_commit_sha,
      published_at = reference_time
  where reserved_batch_id = requested_batch_id
    and status = 'publishing';

  update reader_private.plan_items
  set active = false,
      published_edition_id = requested_edition_id,
      published_commit_sha = requested_commit_sha
  where batch_id = requested_batch_id
    and active;

  perform reader_private.write_audit(
    'plan_batch', requested_batch_id, 'finalized', 'reader-plan'
  );

  return jsonb_build_object(
    'batchId', requested_batch_id,
    'status', 'finalized',
    'commitSha', requested_commit_sha
  );
end
$$;

create function reader_private.release_plan(requested_batch_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  reference_time timestamptz := statement_timestamp();
  selected_batch reader_private.plan_batches%rowtype;
begin
  perform 1
  from reader_private.submissions as submission
  join reader_private.plan_items as item
    on item.submission_id = submission.id
  where item.batch_id = requested_batch_id
    and item.active
  order by submission.id
  for update of submission;

  select * into selected_batch
  from reader_private.plan_batches as batch
  where batch.id = requested_batch_id
  for update;

  if selected_batch.id is null then
    raise exception using errcode = '22023', message = 'unknown_batch';
  end if;

  if selected_batch.status in ('released', 'expired') then
    return jsonb_build_object('batchId', selected_batch.id, 'status', selected_batch.status);
  end if;

  if selected_batch.status <> 'reserved' then
    raise exception using errcode = '55000', message = 'batch_not_releasable';
  end if;

  update reader_private.submissions
  set status = 'pending',
      reserved_batch_id = null,
      reserved_at = null,
      lease_expires_at = null
  where reserved_batch_id = requested_batch_id
    and status = 'reserved';

  update reader_private.plan_items
  set active = false,
      invalidated_at = reference_time
  where batch_id = requested_batch_id
    and active;

  update reader_private.plan_batches
  set status = 'released',
      released_at = reference_time,
      invalidation_code = 'publisher_released'
  where id = requested_batch_id;

  perform reader_private.write_audit(
    'plan_batch', requested_batch_id, 'released', 'reader-plan'
  );

  return jsonb_build_object('batchId', requested_batch_id, 'status', 'released');
end
$$;

create function reader_private.delete_submission(deletion_hash_hex text)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  reference_time timestamptz := statement_timestamp();
  decoded_hash bytea;
  target_id uuid;
  target_status reader_private.submission_status;
  target_batch_id uuid;
  locked_submission reader_private.submissions%rowtype;
  locked_batch reader_private.plan_batches%rowtype;
begin
  if deletion_hash_hex is null or deletion_hash_hex !~ '^[0-9a-f]{64}$' then
    return jsonb_build_object('outcome', 'accepted');
  end if;

  decoded_hash := decode(deletion_hash_hex, 'hex');

  select submission.id, submission.status, submission.reserved_batch_id
    into target_id, target_status, target_batch_id
  from reader_private.submissions as submission
  where submission.deletion_token_hash = decoded_hash
  limit 1;

  if target_id is null then
    return jsonb_build_object('outcome', 'accepted');
  end if;

  if target_status = 'reserved' then
    perform 1
    from reader_private.submissions as submission
    where submission.reserved_batch_id = target_batch_id
    order by submission.id
    for update;

    select * into locked_batch
    from reader_private.plan_batches as batch
    where batch.id = target_batch_id
    for update;

    select * into locked_submission
    from reader_private.submissions as submission
    where submission.id = target_id;
  else
    select * into locked_submission
    from reader_private.submissions as submission
    where submission.id = target_id
    for update;

    if locked_submission.status = 'reserved' then
      raise exception using errcode = '40001', message = 'retry_delete';
    end if;
  end if;

  if not reader_private.constant_time_equal(
    locked_submission.deletion_token_hash,
    decoded_hash
  ) then
    return jsonb_build_object('outcome', 'accepted');
  end if;

  if locked_submission.status = 'pending' then
    update reader_private.submissions
    set status = 'deleted',
        body = null,
        byline = null,
        deletion_token_hash = null,
        deleted_at = reference_time,
        payload_erased_at = reference_time
    where id = target_id;

    perform reader_private.write_audit(
      'submission', target_id, 'deleted', 'reader-delete'
    );

    return jsonb_build_object('outcome', 'accepted');
  end if;

  if locked_submission.status = 'reserved' then
    if locked_batch.status <> 'reserved' then
      if locked_batch.status in ('publishing', 'finalized') then
        return jsonb_build_object('outcome', 'public_removal_required');
      end if;
      raise exception using errcode = '40001', message = 'retry_delete';
    end if;

    update reader_private.submissions
    set status = case when id = target_id then 'deleted'::reader_private.submission_status
                      else 'pending'::reader_private.submission_status end,
        body = case when id = target_id then null else body end,
        byline = case when id = target_id then null else byline end,
        deletion_token_hash = case when id = target_id then null else deletion_token_hash end,
        deleted_at = case when id = target_id then reference_time else null end,
        payload_erased_at = case when id = target_id then reference_time else null end,
        reserved_batch_id = null,
        reserved_at = null,
        lease_expires_at = null
    where reserved_batch_id = target_batch_id
      and status = 'reserved';

    update reader_private.plan_items
    set active = false,
        invalidated_at = reference_time
    where batch_id = target_batch_id
      and active;

    update reader_private.plan_batches
    set status = 'released',
        released_at = reference_time,
        invalidation_code = 'reader_deleted'
    where id = target_batch_id;

    perform reader_private.write_audit(
      'submission', target_id, 'deleted', 'reader-delete'
    );
    perform reader_private.write_audit(
      'plan_batch', target_batch_id, 'invalidated_by_reader_delete', 'reader-delete'
    );

    return jsonb_build_object('outcome', 'accepted');
  end if;

  if locked_submission.status in ('publishing', 'published') then
    return jsonb_build_object('outcome', 'public_removal_required');
  end if;

  return jsonb_build_object('outcome', 'accepted');
end
$$;

create function reader_private.reject_submission(
  requested_submission_id uuid,
  requested_rejection_code text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  selected_submission reader_private.submissions%rowtype;
begin
  if requested_rejection_code is null
     or char_length(requested_rejection_code) not between 1 and 80
     or requested_rejection_code !~ '^[a-z0-9_-]+$' then
    raise exception using errcode = '22023', message = 'invalid_rejection';
  end if;

  select * into selected_submission
  from reader_private.submissions as submission
  where submission.id = requested_submission_id
  for update;

  if selected_submission.id is null then
    raise exception using errcode = '22023', message = 'unknown_submission';
  end if;

  if selected_submission.status = 'rejected'
     and selected_submission.rejection_code = requested_rejection_code then
    return jsonb_build_object('submissionId', selected_submission.id, 'status', 'rejected');
  end if;

  if selected_submission.status <> 'pending' then
    raise exception using errcode = '55000', message = 'submission_not_rejectable';
  end if;

  update reader_private.submissions
  set status = 'rejected',
      rejection_code = requested_rejection_code,
      deletion_token_hash = null
  where id = requested_submission_id;

  perform reader_private.write_audit(
    'submission', requested_submission_id, 'rejected', 'reader-plan'
  );

  return jsonb_build_object('submissionId', requested_submission_id, 'status', 'rejected');
end
$$;

create function reader_private.authorize_handoff(
  requested_batch_id uuid,
  requested_bundle_digest text,
  requested_action text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  selected_batch reader_private.plan_batches%rowtype;
begin
  if requested_bundle_digest is null
     or requested_bundle_digest !~ '^[0-9a-f]{64}$'
     or requested_action not in ('upload', 'download', 'delete') then
    raise exception using errcode = '22023', message = 'invalid_handoff';
  end if;

  select * into selected_batch
  from reader_private.plan_batches as batch
  where batch.id = requested_batch_id;

  if selected_batch.id is null then
    raise exception using errcode = '22023', message = 'unknown_batch';
  end if;

  if requested_action in ('upload', 'download')
     and selected_batch.status not in ('reserved', 'publishing') then
    raise exception using errcode = '55000', message = 'handoff_not_available';
  end if;

  return jsonb_build_object(
    'objectPath', selected_batch.id::text || '-' || requested_bundle_digest || '.zip'
  );
end
$$;

create function reader_private.run_retention(reference_time timestamptz default statement_timestamp())
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  expired_pending integer := 0;
  erased_rejected integer := 0;
  erased_published integer := 0;
  deleted_receipts integer := 0;
begin
  perform reader_private.reclaim_expired_leases(reference_time);

  update reader_private.submissions
  set status = 'expired',
      body = null,
      byline = null,
      deletion_token_hash = null,
      payload_erased_at = reference_time
  where status = 'pending'
    and submitted_at <= reference_time - interval '90 days';
  get diagnostics expired_pending = row_count;

  update reader_private.submissions
  set body = null,
      byline = null,
      deletion_token_hash = null,
      payload_erased_at = reference_time
  where status = 'rejected'
    and payload_erased_at is null
    and submitted_at <= reference_time - interval '30 days';
  get diagnostics erased_rejected = row_count;

  update reader_private.submissions
  set body = null,
      byline = null,
      deletion_token_hash = null,
      payload_erased_at = reference_time
  where status = 'published'
    and payload_erased_at is null
    and published_at <= reference_time - interval '30 days';
  get diagnostics erased_published = row_count;

  delete from reader_private.audit_events
  where occurred_at <= reference_time - interval '365 days';

  delete from reader_private.submissions
  where coalesce(published_at, deleted_at, payload_erased_at, submitted_at)
        <= reference_time - interval '365 days'
    and status in ('published', 'rejected', 'deleted', 'expired');
  get diagnostics deleted_receipts = row_count;

  delete from reader_private.plan_batches
  where created_at <= reference_time - interval '365 days'
    and status in ('finalized', 'released', 'expired');

  perform reader_private.write_audit(
    'retention', null, 'retention_completed', 'reader-retention'
  );

  return jsonb_build_object(
    'expiredPending', expired_pending,
    'erasedRejected', erased_rejected,
    'erasedPublished', erased_published,
    'deletedReceipts', deleted_receipts
  );
end
$$;

revoke all on all tables in schema reader_private from public, anon, authenticated, service_role, reader_edge;
revoke all on all sequences in schema reader_private from public, anon, authenticated, service_role, reader_edge;
revoke all on all functions in schema reader_private from public, anon, authenticated, service_role, reader_edge;

grant execute on function reader_private.submit_submission(text, text, text, text, boolean, text)
  to reader_edge;
grant execute on function reader_private.delete_submission(text)
  to reader_edge;
grant execute on function reader_private.reserve_plan(text)
  to reader_edge;
grant execute on function reader_private.authorize_publish(uuid, text)
  to reader_edge;
grant execute on function reader_private.finalize_plan(uuid, text, text, text)
  to reader_edge;
grant execute on function reader_private.release_plan(uuid)
  to reader_edge;
grant execute on function reader_private.authorize_handoff(uuid, text, text)
  to reader_edge;

select cron.schedule(
  'ddb-reader-retention-daily',
  '17 4 * * *',
  $retention$select reader_private.run_retention();$retention$
)
where not exists (
  select 1 from cron.job where jobname = 'ddb-reader-retention-daily'
);
