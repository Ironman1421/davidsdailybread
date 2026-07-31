begin;

select plan(59);

select has_schema('reader_private', 'reader_private schema exists');
select is(
  (select count(*)::integer from pg_catalog.pg_tables where schemaname = 'reader_private'),
  4,
  'only the four approved private tables exist'
);

select ok(
  not has_schema_privilege(role_name, 'reader_private', 'USAGE'),
  format('%s has no schema usage', role_name)
)
from (values ('anon'), ('authenticated'), ('service_role')) as roles(role_name);

select ok(
  has_schema_privilege('reader_edge', 'reader_private', 'USAGE'),
  'reader_edge may resolve allowlisted private routines'
);

select ok(class.relrowsecurity, format('%s has RLS enabled', class.relname))
from pg_catalog.pg_class as class
join pg_catalog.pg_namespace as namespace on namespace.oid = class.relnamespace
where namespace.nspname = 'reader_private'
  and class.relname in ('submissions', 'plan_batches', 'plan_items', 'audit_events')
order by class.relname;

select ok(class.relforcerowsecurity, format('%s forces RLS', class.relname))
from pg_catalog.pg_class as class
join pg_catalog.pg_namespace as namespace on namespace.oid = class.relnamespace
where namespace.nspname = 'reader_private'
  and class.relname in ('submissions', 'plan_batches', 'plan_items', 'audit_events')
order by class.relname;

select ok(
  not (
    has_table_privilege(role_name, table_name, 'SELECT')
    or has_table_privilege(role_name, table_name, 'INSERT')
    or has_table_privilege(role_name, table_name, 'UPDATE')
    or has_table_privilege(role_name, table_name, 'DELETE')
  ),
  format('%s has no table access to %s', role_name, table_name)
)
from (values ('anon'), ('authenticated'), ('service_role')) as roles(role_name)
cross join (values
  ('reader_private.submissions'),
  ('reader_private.plan_batches'),
  ('reader_private.plan_items'),
  ('reader_private.audit_events')
) as tables(table_name);

select ok(
  not has_function_privilege(role_name, routine_name, 'EXECUTE'),
  format('%s cannot execute %s', role_name, routine_name)
)
from (values ('anon'), ('authenticated'), ('service_role')) as roles(role_name)
cross join (values
  ('reader_private.submit_submission(text,text,text,text,boolean,text)'),
  ('reader_private.delete_submission(text)'),
  ('reader_private.reserve_plan(text)'),
  ('reader_private.authorize_publish(uuid,text)'),
  ('reader_private.finalize_plan(uuid,text,text,text)'),
  ('reader_private.release_plan(uuid)'),
  ('reader_private.authorize_handoff(uuid,text,text)')
) as routines(routine_name);

select ok(
  has_function_privilege('reader_edge', routine_name, 'EXECUTE'),
  format('reader_edge may execute %s', routine_name)
)
from (values
  ('reader_private.submit_submission(text,text,text,text,boolean,text)'),
  ('reader_private.delete_submission(text)'),
  ('reader_private.reserve_plan(text)'),
  ('reader_private.authorize_publish(uuid,text)'),
  ('reader_private.finalize_plan(uuid,text,text,text)'),
  ('reader_private.release_plan(uuid)'),
  ('reader_private.authorize_handoff(uuid,text,text)')
) as routines(routine_name);

select ok(
  not (
    has_table_privilege('reader_edge', table_name, 'SELECT')
    or has_table_privilege('reader_edge', table_name, 'INSERT')
    or has_table_privilege('reader_edge', table_name, 'UPDATE')
    or has_table_privilege('reader_edge', table_name, 'DELETE')
  ),
  format('reader_edge has no direct table access to %s', table_name)
)
from (values
  ('reader_private.submissions'),
  ('reader_private.plan_batches'),
  ('reader_private.plan_items'),
  ('reader_private.audit_events')
) as tables(table_name);

select is(
  (select count(*)::integer from pg_catalog.pg_policies where schemaname = 'reader_private'),
  0,
  'no browser-readable RLS policies exist'
);

select * from finish();
rollback;
