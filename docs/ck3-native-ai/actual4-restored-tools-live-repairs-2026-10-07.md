# Actual 1.20.0.4 restored-tool live repairs — 2026-10-07

Scope: finish migration of the existing enabled MCP tools, then hand off for
vacation. No new gameplay activities or G2 days are authorized by this work.
The original Robert campaign remains paused at date_raw 53288256.

R0060 used source 4c78d08b48a4b3ccde48af922542c1bfbdb5b92a, the qualified
entry11 runtime and the actual Steam 1.20.0.4 executable SHA
98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518.
It restored all 84 old enabled game descriptor tokens; hello contains 88 tokens
including three bridge tokens and the single added core-frame game query.
The paused full snapshot and exact 208-tool registration passed. The following
real failures required narrow production repairs; original RED artifacts remain.

| Existing path | Actual failure | Minimum repair | Verification boundary |
| --- | --- | --- | --- |
| Title-holder V1 | R0060 response013: unsupported native gameplay step | Admit exact .4 in both dispatch and handler; render the existing title-holder result with actual .4 build identity | Source repair authored; actual retry pending |
| Event-window V1 | next02 registered normal frame rejected after nine checks | Strict Python admits the proven .4 provenance and supported field kinds; exact .4 renderer changes the historical idler locator 44BC408 to mapped 44BC418 only for the event-window schema | Reuse existing fixture object; relink and regenerate the two whole frames before consumer retry |
| Combat simulation V2 | R0060 response021 rejects armies[0].knights.members[0].effectiveness_context.schema | Preserve canonical ck3_12003_knight_effectiveness_context_v1 and ck3_12003_knight_current_model_association_v1 after executable identity rendering | Actual V2 retry pending; previously accepted route/contact/Phase fixture results are retained |

These nested Knight and owned-regiment schema names are semantic contracts,
independent of executable identity. Changing the backend/version/SHA must not
rename them. Bridge serialization emits the two Knight names and the existing
strict consumers require those exact names. The second Knight association is
emitted inside the same real effectiveness-context path, so both named strings
are repaired together. This does not change any schema fields or relax checks.

The event-window source proof is frozen in
`upstream-build-migration/event-window-12004/SOURCE-CLOSURE.json`; its production
repair packet is `event-window-production-provenance-fix-12004/`. The title
dispatch patch is in `all-existing-live-review/title-steward/`. All these paths
are beneath `Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/`.

Real failure evidence: `upstream-build-migration/managed-full-h9613-alltools09/`
`operator/gameplay-responses/013-title-holder.json` and `021-normal-phase-v2.json`;
window failures are `upstream-build-migration/events-phase-existing-next01/` and
`events-phase-existing-next02/`. The first window hello generation0 and Phase
missing-output-directory errors were external harness errors; Phase native and
registered V2 retry passed in next02. They do not replace the real window
production repair above. Events and Pending positive fixtures also passed and
are not replayed. Synthetic fixtures provide no production action/OODA credit.

Final qualification and vacation handoff will record the successor source and
runtime pins, actual affected-path retries, unchanged saved days and normal
owned-session shutdown. This document does not claim migration complete.
