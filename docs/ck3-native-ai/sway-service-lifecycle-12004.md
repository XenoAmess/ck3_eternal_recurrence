# Sway retained state and relation material on normal Service turns

2026-10-08, ISO 2026-W41. Source implementation only; its new offline compound
is authored and has not run. Existing 1.20.0.4 tool migration remains accepted.
This work adds a NW2 consumer path and grants no additional live or G2 credit.

The selected blocker is concrete: the existing exact-instance completion tool
returns retained termination, while the material consumer previously always
recorded `instance_terminal_outcome_observed=false`. The normal registered
`ck3_auto_turn` path had no Sway following-turn hook. The managed runner had a
separate call after gameplay, so staging a material record alone did not wire
the ordinary Service or a new cold Service instance.

The native input tree comes from the existing [Sway material research](sway-material-formal-consumer-12004.md),
[retained-row reader](sway-terminal-retained-row-12004.md) and
[actual4 binding](sway-adopted-mcp-migration-12004.md). Those exact-build branches
were reviewed before this consumer change. No native address or native query
was added, and no Start/Cancel decision was introduced.

```mermaid
flowchart TD
  L[Original resolved action: player, target, full ID, generation] --> Q
  Q[Existing exact-instance completion read] --> J{Native full instance join}
  J -->|same player or cleared owner, status1| T[Retained terminated_unattributed]
  J -->|same player, status0| C[Continuing instance]
  J -->|purged or reused| A[Absence or reuse observation]
  T -. no persisted cause .-> U[unknown completed / failed / cancelled cause]
  A -. absence supplies no terminal proof .-> U
  C --> S[Latest instance observation]
  A --> S
  T --> S
  T --> H[Preserved terminal evidence under original action]
  O[Existing opinion read: named Sway and blocker modifiers] --> M
  S --> M[Actor, target, date, exact build and SHA join]
  H --> M
  M --> B[Independent named relation material]
  B --> E[Normal Service auto_turn executes existing selected step]
  H --> E
  E --> F[Existing later paused same-player frame predicate]
  F --> W[Consume start, material and terminal independently]
  W --> P[Atomic original ledger; reopen after cold Service creation]
```

The two existing registered completion/opinion callbacks now delegate through
Service wrappers. Each wrapper makes its original Driver call once, returns
the original normalized body unchanged, and stages matching facts only when
the managed directory has the original resolved once-start receipt. Tool
names, arguments, permissions, annotations and native schemas are unchanged.

`resolved.latest_instance_observation` retains the latest completion body.
`resolved.terminal_intervention` carries its independent consumption state;
once a positive retained terminal is observed, a later purge/reuse preserves
that original evidence. A purge alone remains nonterminal. Full scheme ID and
generation must belong to the original action. These records never recover a
missing terminal cause by subtracting total opinions or reading row absence.

The existing named-material builder is shared by the active census recorder
and the completion/opinion join. Actor, target, raw date, exact build and SHA
must agree, using the existing material pair semantics. Each independent
query keeps its native revision; the two reads are not advertised as one native
transaction. Observed legal absence remains zero, present zero remains zero,
and an unobserved modifier remains unobserved. Positive named Sway material
and unattributed termination can coexist. The opinion body itself still says
it has no terminal observation.

`Service.auto_turn` and `auto_nonwar_turn` now call the existing following-turn
consumer after an executed outcome. The post-turn snapshot excludes native
command history and is read only when the original ledger has an unconsumed
start, material or instance observation. Blocked/intercepted turns do not
consume it. A duplicate semantic completion/opinion read does not rearm a
consumed record. A fresh Service uses the same atomic ledger, so previously
consumed Start and newly staged terminal/material records remain independent.

The existing consumer requires a later native revision or raw date and the
same living player on a paused ready map. Service's `executed` result can also
represent a query step. Its Sway attachment alone proves bookkeeping through
the selected turn; it does not certify world progression, native completion
cause, an additional NW2 loop, or any new gameplay outcome.

The new compound at
`ck3_autonomous_player/tests/unit/test_sway_service_lifecycle_12004.py` exercises
the real registered MCP callbacks and Service dispatcher using explicitly
synthetic normalized inputs/planner selection/backend frames. It covers named
benefit, retained terminal, independent already-consumed Start, new cold
Service, repeated-read consumption, later purge, and blocked return. It is
`AUTHORED_NOTRUN`; Root owns its first execution. The existing actual4 native
current/terminated/reused/purged whole-packet qualification is reused from the
retained-row topic and will not be rerun for this Python change.

No compiler, tests, imports, local game, SDK, process control or EXE extraction
was performed by this source lane. Remaining acceptance is the one new offline
compound, then a future allowed normal gameplay turn with real staged reads.
Exact end cause remains an explicit native research gap, independently of
using current named relation material and retained termination.
