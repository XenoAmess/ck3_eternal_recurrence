# Child education definition lookup in the general FocusDB

This source-only leaf reads the exact 1.20.0.4 general FocusDB for an explicit
education key. It returns a definition pointer only after a complete bounded
scan finds exactly one matching canonical key and two samples agree.

The retained `1445E40` window body loads `module+5C67188` at `14460DA`, reads
the database's `F08` pointer and signed `F14` count at `1446128/144612F`, forms
the 8-byte pointer extent at `1446136`, and reads each definition at `1446150`.
The window's selected-lifestyle comparison of definition `+7F8` starts at
`1446153`, after that general database traversal. The new leaf stops at the
general database/key lookup. The existing actual4 stock readonly producer
supplies the `F08/F10/F14` span layout and the existing 64-row software bound.

`ReadChildEducationFocusDefinitionReadonly12004` reuses the existing public
actual4 MSVC stable-key reader at definition `+18`. Its requested keys are
`education_diplomacy`, `education_martial`, `education_stewardship`,
`education_intrigue` and `education_learning`, matching the current education
consumer's `_EDUCATION_KEYS`. This request set does not prove current database
membership.

The input consists of the guarded memory callback, module base, the existing
exact-build admission and executable hash, and one requested key. The outer
native host binds the actual child full ID, played controller and current
paused main-thread frame. It must keep any resolved pointer inside that frame
and pass it only to the already qualified native command/validator path.
Pointers and database addresses are internal observations and are never wire
fields or reusable action inputs.

Each sample reads the database pointer and raw span before and after all rows.
Two complete samples must agree on the database, span, all definition pointers
and all canonical keys. Negative or inconsistent counts/capacities, more than
64 rows, missing nonempty data, unreadable rows/keys and changed samples remain
unavailable. A stable valid empty table or complete scan with no match is
`missing`; multiple exact matches are `ambiguous`; exactly one match is
`resolved`. Only `resolved` sets `available`, `definition_identity` and the
unique index together. No partial scan supplies an actionable pointer.

The implementation does not read selected lifestyle, player progression or
age, construct fallback objects, enumerate a GUI, invoke native code, or decide
child command legality. Original native validators remain responsible for
legality. Source and API dependencies are frozen in the external owner64
`SOURCE-FIRST.json`; the minimal patch is delivered to owner35 for the actual
child host and to the common build owner for its single additional source TU.

Status: `SOURCE_CLOSED_AUTHOR_NOT_RUN`. No tests, production imports, compiler,
native invocation, process connection or game activity ran for this leaf.


Root source adoption: **SOURCE_ADOPTED_NOT_RUN**. The connected native query,
original command, independent receipt, exact executor registration, guarded
Runtime source list, strict Driver and ordinary family caller are adopted
together. No test, import, build, deployment or game operation followed.

2026-10-19 source-scope correction: the historical “general FocusDB” label
above does not prove that its F08 span contains all education definitions.
It was adopted from the adult lifestyle-window traversal. Closed actual4107
retained current `education_intrigue` while target `education_stewardship`
was missing from that resolver; original target legality remained unknown.
New exact.4 source identifies `CharacterFocusWindow.GetFocus(int32)` as a
window-owned D0/DC collection getter, not a global education registry.
See [the bounded source audit](child-education-target-resolver-source-2026-10-19.md)
for machine ID, UTC, exact bytes and the remaining collection-producer gap.
The old capture and adoption facts remain historical; neither “missing”
nor this new getter supplies education-choice or focus-write qualification.
