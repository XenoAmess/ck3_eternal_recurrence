# Adopted Activity and Feast MCP migration to CK3 1.20.0.4

Source-first migration, October 7, 2026 (Asia/Shanghai). The implementation
baseline is `caa4adc3d1278e324cf4ec19774028e9b9138e28`. The current frozen tuple
is CK3 **1.20.0.4**, Steam **25734779**, executable SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The earlier .2/.3 contracts and live receipts remain historical evidence.

The authoritative adopted coverage assigns sixteen existing enabled flags to
this package: passive slot-12 cost, guest candidate, guest opinion, guest rule
provenance and toggle, planner Open, Stage-1 option read and confirm, Stage-2
destination, gate, location and option read, and Stage-5 CanStart, Gold, full
Feast cost and Start. Their current production route also returns the existing
Start-input and hosted-post/target views. This migration preserves these
schemas, actions and policy. It adds no Activity decision or policy.

The source ledger is external at
`Z:/ck3_mod_rewrite_process_assets/g2-migration-20261007/activity/`.
`common-native/SOURCE-TREE.md` and `PARENT-SOURCE-PLAN.md`,
`planner-native/SOURCE-TREE.md`, `guest-cost-native/SOURCE-TREE.md`, and
`python/SOURCE-TREE.md` were sealed before their implementation. Each finite
mapper receipt retains original ranges, candidates, decoded member operands,
relative/RIP targets, unique I/O and partial attempts. Existing core-global and
command-layout proofs are reused; no whole-image read, hash or runtime contact
is part of this package.

```mermaid
flowchart TD
 A[Existing 16 enabled Activity flags] --> B[Existing private step grammar]
 B --> C[Same application-main mailbox and selected actor frame]
 C --> D[Exact actual .4 identity and finite Activity profile]
 D --> P[Planner owner, selected type and options]
 D --> G[Guest rules, candidate, opinion and travel]
 D --> K[Passive aggregate and configured named costs]
 P --> S[CanStart and existing Start commit]
 G --> S
 K --> S
 S --> H[Independent full Activity ID / host / type / terminal readback]
 H --> W[Existing wire schemas and production Python consumers]
 G --> T[Actual .4 opinion / traits / XP factories]
 W -. requires Root qualification .-> R[First native build, fixture and actual MCP validation]
```

The existing planner .2 ABI retains full IDs, owner `+A0`, handler slots `+3C0`
and `+3D8`, selected type `+1500`, stage `+1AE8`, option rows and actual widget
visibility. Actual .4 mapped code retains those member operands. Direct entry
mappings include CanStart `11B8670 -> 11B8650`, selected province
`11B6C80 -> 11B6C60`, Commit `11B8D90 -> 11B8D70`, and unchanged typed dispatch
`AF39E0`. The ScriptOption identifier belongs to ScriptIdentifierTable:
`3F8A800 -> 3F8A7E0` and `3F8A6F0 -> 3F8A6D0`. It is not the generic type-name
domain. Relative guard displacements are recalculated from the paired actual
instruction site and target while all opcode/member bytes remain exact.

CanStart contains 800 code bytes followed by six DWORD image-relative branch
targets. Its code uses the paired table addresses `11B8990 -> 11B8970`; the
separate temporary vptr `476BAA0 -> 476BAB0` is corroborated by the actual
paired RIP base `476BA70 -> 476BA80`. These two operands and the branch table
are explicitly compared as code/data, not blindly normalized. The selected
Stage-5 source branch is `11B88E8 -> 11B88C8`.

Guest/cost source has a concrete historical literal correction: the actual
.3/.4 rule sentinel is `5D34048`, whereas the old .2 literal was `5D33F48`.
The .4 database getter has displacement byte `3D` instead of `1D`. Rule
vptrs `48B2F20 -> 48B2F30` and `48B2EC0 -> 48B2ED0` come from paired native
operands. Actual selected guest refresh, activation, independent readback,
membership, configured signed cost values and travel ABI remain distinct from
the passive aggregate. The native travel call still begins at `9DFF87`, now
targeting `2BBADC0`. Arrival constructor calendar-table operands changed; its
full equivalence is not claimed because the production view reads raw copied
dates and does not call that constructor.

Actual constructor operands close planner vptrs `45325C8 -> 45325D8` and
`45326A0 -> 45326B0`, HostView `457A138 -> 457A148` and `457A110 -> 457A120`,
and ActivityType `48BFE50 -> 48BFE60`. The remaining identity packet closes
idler `44BC408 -> 44BC418`, handler `44BA890 -> 44BA8A0`, ScriptOption
`48BFD18 -> 48BFD28`, Activity `472E130 -> 472E140` and payload descriptor
vptr `44E6F38 -> 44E6F48`. The two RTTI type descriptors remain `5514438` and
`5514460`; their named classes, linked COL/hierarchies and actual paired stores
are retained in `planner-native/REMAINING-IDENTITY-PROOF.json`. Pointer copy and
move remain `878290`. No common `.rdata` or code delta is assumed.

The explicit .4 GiftOpinion factory uses total opinion `28BC470`, modifier
lookup `25A2EE0`, group lookup `2949A80`, sum `2596290`, database `5D207E0`,
modifier vptrs `48C5380`/`48C5348`, and receiver vptrs `473DE18`/`473DDE0`.
All eleven windows reuse retained exact caches with zero new EXE reads. It
retains recipient-to-actor direction, full-ID resolution, repeated scalar and
keyed modifier semantics. Feast's stable-key hash directly uses the already
closed `3F7E220`; it does not claim an unclosed EventWindow producer.

The independent .4 phase-character factory returns the existing software
Bindings DTO while directly admitting the current SHA and six current
functions. Trait database `89E5B0`/slot `5C67528`, presence `28BB1D0`, tracks
`28BB0D0`, track index `30E56F0`, human-player `2BAA6F0` and knight context
`28BFC50` are bound explicitly. The full tracks/index paths are 251/193 bytes;
the insufficient first-fragment receipts remain preserved. Existing raw trait
definition/name/presence/XP readers are reused. This does not migrate the
separate phase-definition identifier binder.

Python Activity leaves consume the central exact-build provenance contract.
Their existing schemas require no duplicate version table. The single new
compound test exercises current-build production cost, guest, Start-input,
submit and hosted/terminal consumers. Its retained historical payloads plus
synthetic actual .4 hello are fixture inputs, not new .4 native or live proof.
Native fixtures likewise use fake memory and fixture-owned executable thunks.

The single new production Python case first passed on October 7 (outer
2.1765844 seconds, unittest 1/1). Its receipt is
`python/new-production-case-01/RESULT.json`; no old case was run. The unique
native target recipe is `ROOT-HOOK-AND-NATIVE-TARGET.md`, with three new
production fixture groups and one main. Child native build/execution is zero.

Until Root's first formal build and fixtures, this package is a source-backed
implementation candidate. No actual .4 MCP or live action qualification is
claimed. Start acknowledgement remains pending until independent hosted
readback; terminal identity does not itself prove an opinion/resource gain.

Root's first new native fixture on October 7 returned RED in the planner/start
group (exit 1, 0.1523465 seconds), with `actual4 planner/start fixture failed`.
The finite Activity switch omitted the already closed commit mapping
`11B8D90 -> 11B8D70`; the production Start ABI guard consequently attempted a
read at the module base, before capture or commit. The existing 329-byte paired
proof is `planner-native/mapped-functions/planner_feast_commit-DETAIL.json`.
The source fix restores that one mapping and adds an independent literal
entry assertion to the existing planner/start fixture. No guard, frame,
reserve, guest-route, repeated-capture or independent postcondition is relaxed.
This correction has not been built or executed in the child; Root's affected
native fixture retry and actual .4 MCP qualification remain pending. The first
RED artifact is retained at
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/joint-domain-first01/activity_new/`.

Root's affected native retry FIRST02 passed the planner/start and guest/cost
groups, then returned RED in hosted/resources (exit 1, 0.1703046 seconds).
Its first hosted query failed the exact-build guard because the finite switch
also omitted host CharacterID write site `23F0195 -> 23F0175`. The hosted
fixture's existing source plan independently pins `23F0175:418987A8030000`.
This source fix restores that one mapping and adds an explicit hosted guard
address assertion. Full identity, attendance, signed balances, known zero and
later terminal assertions remain unchanged. The retained failure is
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/joint-domain-first02/activity_new/`.
No child build, execution or new native proof collection was performed;
Root's affected native retry and actual MCP qualification remain pending.

R0054's actual production read on the original paused Robert 29829 campaign
now qualifies the hosted-post read as a `production-live primitive`: the
actual `.4` response reports date `53288256`, native revision 2, queried
public revision 3, no hosted Activities, Gold `83556691`, Piety `43106250`,
prestige `305510310` and stress zero. Treasury, barter and Reveler XP remain
unavailable; this read does not qualify planning or an Activity action. Reuse
`upstream-build-migration/managed-full-h9613-entry02/operator/gameplay-responses/supplement-02-activity-hosted-state.json`;
do not repeat this passed read.

The following guest-source read returned the actual native RED
`exact_activity_feast_guest_candidate_build_unavailable`. Its retained
response is `supplement-03-activity-guest-candidate-source.json` in the same
directory. That error is produced before planner lookup when the required
passive-cost observer is not installed, so it does not prove planner absence.
The existing enabled private route, current SHA and modern build predicate
already admit actual `.4`; its startup descriptor branch instead returns
after journal installation without installing the existing Activity passive
cost and rule-provenance observers. Their frame callback also lacks the
explicit CoreBindings4 reader branch. The unchanged strict04/strict05
configuration enables cost passive, guest candidate and rule provenance.

The minimal central correction is to bind CoreBindings4, use its explicitly
qualified frame reader, and call both existing observer installers before
that actual `.4` startup return under their current flags. This does not need
an Activity leaf or profile change. The cost installer already selects and
verifies actual `.4` refresh `11BA6B0`, return `11B5B3F` and planner/type vptrs
`45325D8`/`48BFE60`. The rule installer already selects refresh `2BBD190`,
effect `3765860` and caller returns `11B8311`/`2BBD30A`, including their exact
prologue and call-site checks. Reuse the held `guest-cost-native` function-map
and `SOURCE-QUALIFICATION.json` proofs; no new EXE read is required. The exact
shared-hook recipe and proof paths are external at
`upstream-build-migration/actual-live-review/ACTIVITY-PASSIVE-CORE4-SHARED-HOOK.md`.

The central owner integrated this correction in
`f328c059b8cd54a4a73bcd80c2738df0a5bc734f`. It was initially recorded as
`source-fix NOT RUN`; the first Root-owned actual retry now returns a valid
`activity-feast-guest-candidate-private-read-v1` response with
`status=planner_unavailable`. Its retained body is
`upstream-build-migration/managed-full-h9613-binding04/live-failed01/retry-failed-feast-guest-candidate.json.body.json`.
It preserves actual `.4` identity, Robert 29829, paused date `53288256`,
native revision 2, public revision 3 and post `native:2`. Root's accepted full
snapshot is the new third snapshot; the two earlier startup snapshots and the
previous guest build-unavailable RED remain retained.

This actual read qualifies a `production-live primitive` returning the typed
planner availability boundary. `normal_refresh_sequence`, `source_fingerprint`,
`native_filtered_pre_invitation` and `candidate` are all null, so candidate
eligibility, costs, native filtering source and candidate-ready are not
qualified. The source status combines an unobserved diagnostic, absent
planner, non-Stage-5 planner, detached or hidden widget and a non-Feast type;
the response does not distinguish those branches. Its `planning_stage=5` is
the requested stage, not an observed planner stage. No additional source
fault follows from this response on the existing campaign without an opened
Feast. Root's retry used the G110-r4 runtime (reported source prefix `9cb`, DLL
prefix `4c39596`, PID 161728); the child performed no build, test, SDK query or
game action. Hosted and fixtures were not replayed. No Activity action,
campaign date or G2 progress credit is added.

## October 11: native completion QWORD in the existing lifecycle read

Root adopted seven production source files for this path as
`SOURCE_ADOPTED_NOT_RUN`. The currently compiled Native84/SDK84 source remains
`594979b0b3d4c5a395639f30b9d5d864b8a31f6d`; that compiled baseline does
not qualify these new fields. No new build, test, project import or game query
was performed for this increment.

The held actual .4 completion fragment writes `Activity+421=1` at
`23F6D3B`, then stores the original RAX QWORD at `Activity+408` at
`23F6D43`. The original 15-byte fragment contains no RAX definition. A subsequent exact
997-byte actual .4 source capture closes its producer: at `23F6D34`, RAX loads
the QWORD at module RVA `5C7E338`. Both the empty loop and normal loop end
reach that load; no call, arithmetic or scaling changes the value before the
store. Its units and interpretation remain unknown. This is a raw completion
stamp input, not a completed timestamp contract; query date and object absence
cannot supply the missing meaning.

The existing hosted and requested-target readers now copy that QWORD under
their existing player, host and full Activity identity checks. They publish
`native_completion_stamp_observed` and `native_completion_stamp_raw`
in the existing same-response views. A successful read preserves all unsigned
64 bits, including zero. The target reader requires both existing samples to
read the same value. Optional read failure or change leaves the stamp
unavailable and preserves the prior identity status and terminal flags.
The wire represents an unavailable raw value as null; older packets may omit
both new fields.

Strict decoding and exact identity normalization carry the pair into
`lifecycle.latest_identity_observation`. Once a value is known, the durable
consumer also retains the whole original source observation in
`lifecycle.native_completion_stamp_observation`, with its original query
date and revision. A later failed read leaves the latest observation unknown
without erasing or relabeling that historical value. The existing Service
result already exposes the lifecycle observation; no additional query or
Service gate was introduced. Completion/invalidation overlap, reward
attribution and action or material outcome credit remain separate.

The exact source-first receipts are the October 11 source-round
`institution-activity-terminal-source-01/DELIVERY.json` files under
`continuation-12` (reader), `continuation-47` (two real serializers)
and `continuation-51` (three Python consumers). The aggregate reference is
`continuation-16/background-g2-source-round-20261011-0907/institution-activity-terminal-source-01/COMPLETION-STAMP-ADOPTION.json`
under `D:/codex-ck3-background-spill/native71-continuation-20261010`.
The raw producer source is `common-native/parent-map01/activity_complete_flags-DETAIL.json`
in the retained Activity ledger. The completed producer closure is recorded in fresh `continuation-03`
`institution-activity-terminal-source-01/SOURCE-CONTRACT.json`, with the
exact `[23F6980,23F6D65)` source packet. The remaining time interpretation
requires an existing standard date/clock contract for the exact `5C7E338`
QWORD. Pre-callee invalidation observation is an independent source increment;
these seven files do not observe a released object.

## October 11: retained native terminal observation before the first callee

Root applied twelve connected production source files as
`SOURCE_ADOPTED_NOT_RUN`: a fixed native observer, the bounded journal and
existing hosted-post reader, the same-response serializer, strict and durable
consumers, four thin Bridge regions and two Runtime source registrations.
The compiled Native84/SDK84 source remains
`594979b0b3d4c5a395639f30b9d5d864b8a31f6d`. No test, project import,
build, native installation or game query qualified this increment.

The exact archived actual .4 body `[29BF660,29BF7C4)` supplies the cut.
Entry RDX is preserved in RBX as the original Activity and RCX in RSI as
its manager. The zero invalidation arm writes `Activity+422=1` at
`29BF685`. The observer replaces only the five-byte
`LEA RCX,[RSP+50]` at `29BF68C`, after that write and before the first
callee. It preserves the reused register/flag state, copies through the
callback with the original RSI/RBX identities, restores and replays the LEA,
then continues at `29BF691`. The original call remains in place once.
The later callees and their release effects remain unclosed; this observation
does not prove storage release, termination cause, reward or material payoff.

The journal copies the original full DWORD Activity ID and generation, host
DWORD, type, independent completed/invalidation bytes and optional raw
completion QWORD while the object is still borrowed at this cut. Its actual
existing Core/GetPlayer frame restricts capture to the current player's
hosted `activity_feast` on the known owner thread. The 64-record process
lifetime ring preserves the original capture frame and coverage diagnostics.
Its software sequence orders retained records; it is not a native clock.
Missing, detached, overflowed or empty coverage does not prove event absence.

The existing hosted-post response now carries the copied journal. A consumer
can retain a known nonzero completed or invalidated byte after the object
leaves the hosted list only when full ID/generation, host and type match its
persisted Activity. An unread other byte stays null. The source cut, query
date and raw completion QWORD never supply terminal flags. The complete
matching row and its original capture frame survive through the existing
lifecycle and Service observation path; a journal-only result keeps
`restored_activity_observed=false`. This closes the source path for retaining
an observed terminal fact after hosted-object removal. It adds no Activity
action, current campaign completion or payoff credit. The `5C7E338` QWORD
producer above is known, but its time units and interpretation remain unknown.

The source flow below separates the original native call from the owned query
data path. Dashed native edges remain unknown; all new bridge edges are source
connections awaiting authorized runtime qualification.

```mermaid
flowchart TD
    A["29BF685: write Activity+422=1 on the zero-flag arm"] --> B["29BF68C: pre-call cut, original RSI/RBX"]
    B --> C["Observer source: copy player-hosted activity_feast inputs"]
    C --> D["Restore original state and replay LEA"]
    D --> E["29BF691: original native CALL once"]
    E -. "unknown later effects and terminal cause" .-> U["Remaining native callees"]
    C --> J["64 owned records: full identity, read flags, optional Q64, capture frame"]
    J --> Q["Existing hosted query and strict decoder"]
    Q --> M["Match full ID/generation, host and type to durable Activity"]
    M --> L["Retain observed terminal fact; absent object stays restored_activity_observed=false"]
```

Root's direct producer-to-consumer source review found a deterministic
disconnect before adoption: both new journal filters used the literal
`feast`, while the existing reader and strict consumer use
`activity_feast`. Owner 38 corrected only those two comparisons. The final
`activity_terminal_observations_12004.cpp` is 10,191 bytes with SHA-256
`66fdcf59a250772e4152e03e2115729b33b2c28165d86ae6e780b39fc857556d`.
The prior candidate and its source correction remain separate receipts; this
was a source contract failure and correction, not a runtime failure or pass.

The exact twelve mappings, owner patches and the two-line amendment are
linked by `ACTIVITY-PRECALL-TERMINAL-ADOPTION.json` under
`D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-16/background-g2-source-round-20261011-0907/institution-activity-terminal-source-01/`.
It references the source-first deliveries of owners 12, 38, 47, 51, 62 and
60, and owner 29's exact archived cut proof. Root reported all twelve files
successfully applied with exit 0; no local executable qualification followed.
