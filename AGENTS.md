# Repository instructions for contributors and agents

Before interactive work, read `FOUNDER_DOCTRINE.md`, then `CLAUDE.md` for the
production workflow and `BRAND.md` for reader-visible rules. The founder
doctrine is authoritative for mission, ownership, strategy, authorized local
work, and production boundaries.

Interactive work must also follow `operations/program-control.json`, the sole
source of truth for execution order and task state. Only the designated program
controller may change that file, activate work, or select a successor. A worker
executes only its assigned item, returns its completion evidence, and stops.
Workers may report newly discovered work but may not start it or add it to the
queue. At most one item may be `in_progress` at a time.

## Deterministic handoff

At every completed action or task, pause, blocked state, approval boundary, or
end-of-turn handoff, the final user-facing response must end with a
`Recommended next step` section. Select one primary action instead of an
unranked list. Give exact approval wording when approval is required, identify
the item, PR, and immutable commit SHA when applicable, state what must remain
unchanged, and say what the controller will execute and verify next. If no user
action is needed, say `No action required` and name the next verification or
wake condition.

The 2026-08-04 decision authorizes strategy, design, local implementation, and
testing across the durable-moat roadmap. Do not infer approval to publish,
send email, spend money, provision services, install credentials, accept
provider terms, collect live personal data, form an organization, or open a
community surface. Follow the phase gates in `docs/GROWTH_ROADMAP.md`.

Bake sessions follow `BAKE.md` as their complete procedural specification.
