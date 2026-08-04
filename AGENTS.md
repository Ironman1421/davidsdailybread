# Repository instructions for contributors and agents

Before interactive work, read `FOUNDER_DOCTRINE.md`, then `CLAUDE.md` for the
production workflow and `BRAND.md` for reader-visible rules. The founder
doctrine is authoritative for mission, ownership, strategy, and paused work.

Interactive work must also follow `operations/program-control.json`, the sole
source of truth for execution order and task state. Only the designated program
controller may change that file, activate work, or select a successor. A worker
must execute only its assigned item, return its completion evidence, and stop.
Workers may report newly discovered work but may not start it or add it to the
queue. At most one item may be `in_progress` at a time.

## Deterministic handoff

At every completed action or task, pause, blocked state, approval boundary, or
end-of-turn handoff, the final user-facing response must end with a
`Recommended next step` section. Select one primary action instead of offering
an unranked list. State why it is next in program order, provide exact
copy-and-paste approval wording when approval is required, identify the item,
PR, and immutable commit SHA when applicable, state what must remain unchanged,
and say what the controller will execute and verify after approval. If the user
does not need to act, explicitly say `No action required` and identify the next
automatic verification or wake condition. Do not invent work merely to fill
the section.

Do not infer approval to publish, send email, spend money, provision services,
form an organization, or open a community surface. In particular, no newsletter
sending or activation work may proceed without David explicitly reversing the
current decision in the repository.

Bake sessions follow `BAKE.md` as their complete procedural specification.
