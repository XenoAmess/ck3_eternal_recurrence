# Active-war strategic-power query

Status: `production-live primitive; campaign-policy integration pending`; exact build: CK3 `1.19.0.6`, executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

## R0039/R0040 checkpoint-replay boundary (2026-09-21)

R0039 and R0040 establish that the exact-build strategic-power tuple is stable
for repeated reads on one paused frame, but is not byte-for-byte reproducible
after a save and process-replacing cold restore. Both sessions observed actor
`29829`, WarID `16777285`, date `53190816`, score `-3`, duration `822`, and
actor power `10084484600`. The producing R0039 frame reported target base /
network / adjustment / total as `16135200000 / 700000000 / 6053880000 /
22889080000`, ratio `226973`; the restored R0040 frame reported
`14423200000 / 700000000 / 1310400000 / 16433600000`, ratio `162959`.
Each tuple was identical across two immediate reads in its own session.

That change was sufficient to reverse the formal decision: R0039 selected
surrender (`-101825000`) over continue (`-113486500`), while R0040 selected
continue (`-81479500`) over surrender (`-101825000`). The visible army IDs and
states were unchanged, but the terminal R0039 frame did not perform a fresh
army-strength query, so this evidence does not claim identical material army
strengths across the two sessions.

The resulting policy contract is deliberately narrow:

- a terminal authorization is valid only on the live paused frame that
  produced its complete option/power/terms certificate;
- recommendation, authorization comparison, and the one typed terminal
  submission remain on that same driver and frame;
- the post-action material result is checkpointed, then a real new-process
  cold restore proves target continuity and next-turn non-replay;
- a pre-action restore mismatch remains RED and never forces the stale action.

R0040 followed that fail-closed rule: it submitted no terminal action and
cleaned up the CK3 process. The same-session orchestration is an internal,
default-off Python runner path; it changes no native ABI, public MCP schema, or
`open_kaishek` compatibility surface. Focused normal and optimized suites each
pass `130/130`.

R0041 then reached the intended same-session callback with the original
R0039 power tuple and surrender recommendation, but stopped before mutation on
`recommended_action_step_not_advertised`. The cause was query ordering, not a
new game-state mismatch: the callback fetched capabilities before its four
read-only option/power/terms queries refreshed the WarID-bound terminal cache.
The bridge advertised the surrender capability, while its dynamic literal was
still absent from that earlier capability snapshot. The runner now refreshes
capabilities after those four queries and before the action gate. A focused
fixture proves the literal is absent before the terms query and present after
it; the combined normal and optimized suites each pass `142/142`. R0041
submitted no terminal action, retained immutable sources, and cleaned up all
managed processes. Production-live closure remains pending one fresh round.

## Problem and reuse decision

R459 proved the exact outcome of surrendering WarID `33554473`, including the
3000-to-zero event-army loss and the persisted 1825-day truce. It did not prove
that surrender was preferable because the campaign comparison still lacked a
same-frame strategic-power observation for the current opponent.

The existing production-live capability
`game.command.query-war-entry-assessments-v1-N` already calls CK3's exact
strategic evaluator and returns actor/target base power, relationship-network
contributions, totals, target adjustment, distance, and native power ratio.
The first static package incorrectly assumed that the C++ reader accepted any
explicit full-generation CharacterID and that the declarable-only restriction
lived only in Python. R470 disproved that assumption: the native frame freezes
`declarable_target_character_ids`, and the reader returns
`target_not_declarable` before invoking the exact-build evaluator when the
requested active-war opponent is absent from that set. Reusing the evaluator
therefore requires a small native admission change and a new DLL.

## Additive target scope

The one-target query now accepts a CharacterID present in either current
snapshot source:

- `declarable_wars[*].target_character_id`;
- `active_wars[*].primary_opponent_character_id`.

Every result adds `target_scopes`, with stable source values
`declarable_war` and `active_war_primary_opponent`. A target present in both
sources reports both values in that order. Targets outside the union are
rejected before the named-pipe request. The source set is checked again on the
same paused snapshot after the native result returns; a source change rejects
the result.

The native schema-v1 payload retains its frozen
`readiness.targets_declarable_ready` key. For this capability version, that
legacy spelling cannot yet be interpreted as active-war eligibility: R470
failed before a result payload existed. Consumers must keep the active-war
scope runtime-uncertified until the corrected native DLL passes a bounded live
query. The outer `target_scopes` field remains the intended source
classification after that correction.

## Policy boundary

This remains a read-only observation. It does not enable declaration,
surrender, white peace, or any recommendation. For GEN-034 it can fill the
current-opponent strategic-power input, while campaign dominance,
owner-authored budget, and same-frame white-peace comparison retain their own
readiness gates.

Focused contract, native-driver, service, strategy, and official MCP client
tests pass `23/23` in normal Python and `23/23` under `python -O`. No CK3
process was launched for this code package. The next live check is one bounded,
read-only query of R459's durable pre-surrender checkpoint; it is not a long
campaign run.

## Companion compatibility sync

open_kaishek commit `3d54890451d447fbad26575543fbb2d27e853e59`
initially froze this additive MCP boundary. After R470 disproved the assumed
native support, corrective commit
`2fd64da020c75645384ea566288f304c3c17b916` changed the profile to both
native-uncertified and runtime-uncertified and pinned the RED report. Its
focused offline Maven test passes `4/4`.

## Bounded live runner

`run_active_war_strategic_power_live_acceptance.py` reuses the existing single-process cold-checkpoint owner. It allows exactly one CK3 launch and two official MCP strategic-power queries on one unchanged paused frame; it advances no time and permits no mutation command. The shared runner's existing tests pass `4/4` in normal and optimized Python, and the new runner passes import/CLI compilation checks before live use.

## R470 production RED

R470 loaded R459's frozen checkpoint and reached exact-build, capability,
paused-frame, player, active WarID, and primary-opponent identity readiness.
The first official MCP query for CharacterID `28551` failed with
`application-main war-entry query failed:target_not_declarable`. The second
same-frame query was deliberately not attempted; there was no retry, time
advance, or mutation.

The report is
`Z:\ck3_mod_rewrite\_runtime\g2-r470-active-war-power-20260912\report.json`
(SHA-256
`CCF29894130EB673C59FDAD03E39D15A6BEB649392C6A2D02E1DF8A92C7E022D`).
The source checkpoint remained
`FAA32578602EF546D991C364D196292C70C2D491FBCC6D4558FAB31444E14E78`,
and the restored driver state remained
`A5DB3F1E5FEDCD019B60FDAB0380E072D9D8465E330DD6D080AA3D0208994B5E`.
Cleanup is GREEN. Current round R470 is terminated, old round R469 is
terminated, and CK3 inventory is zero.

The minimal corrective boundary is now concrete: freeze declaration targets
and active-war primary opponents as distinct native-frame eligibility sources,
admit a request present in either source, and retain same-frame equality across
all captures. The exact evaluator, one-target limit, paused owner-thread
mailbox, full-generation identity checks, and read-only output remain
unchanged. Only focused native tests and one bounded new-round live query are
required; no campaign-length acceptance is justified for this defect.

## Minimal native correction

The corrected frame now carries separate declaration-target and active-war
primary-opponent vectors. `ReadWarEntryAssessmentsV1` admits the one requested
CharacterID when it is present in either vector; frame-shape validation and
the existing before/middle/after structural equality checks cover both. The
exact evaluator and resolver RVAs, mailbox, one-target cap, wire serializer,
and legacy failure/readiness spellings are unchanged.

A fresh MSVC 19.51 Release build completed all 545 compile/link steps with the
header dependency gate intact. Only the directly affected reader and source
contract CTests were executed; both pass (`2/2`). The candidate DLL is
`Z:\ck3_mod_rewrite\_runtime\native-builds\r471-active-war-power-r2-20260912\xar_ck3_bridge.dll`
(SHA-256
`65C14FE284EA99036DBFBA950B3BE38C3656FA2D064017FD8A38FF21B32B61EF`),
and the injector SHA-256 is
`C4CE2042C2559216E816C29081277E064CD276A0097DB85BD7402DC5C16FE389`.
No CK3 process was started for this build package. The next evidence step is
one bounded R471 read-only checkpoint query with this exact DLL.

The native correction is committed and pushed as
`283904d5438e07c18a49903333eafcaaabb75e80`. The corresponding open_kaishek
profile update is `0d7ed41bc90ce2afdc4cd81d6d31beb2c759a38a`; it pins the
new native sources, ABI ledger, candidate DLL, and keeps native/runtime
certification false until R471.

## R471 production-live closure

R471 loaded the same immutable R459 pre-surrender checkpoint with the corrected
DLL and returned the current active-war primary opponent twice through the
official MCP surface on one unchanged paused frame. Both calls reported
`status=available`, query sequences `1` and `2`, snapshot `native:3`, public
revision `4`, native revision `3`, and date `53183856`. The normalized payloads
are identical.

The observed player CharacterID `29829` has strategic power
`13075500000`; opponent CharacterID `28551` has base/pre-adjustment power
`15460500000`, target adjustment `1310400000`, and total power
`16770900000`. Native ratio `128262` at scale `100000` means the opponent is
1.28262 times the player's measured power. The result classifies the target as
`active_war_primary_opponent`; every native readiness bit is true.

The original report remains RED because the runner audited nonexistent
`history` fields instead of the public snapshot's `native_command_history`.
The underlying history contains exactly the two successful query rows and no
time-advance or mutation command. The minimal harness correction now reads the
canonical field and checks both command literals and `ok=true`; its focused
normal and optimized tests each pass `1/1`. The original report is
`Z:\ck3_mod_rewrite\_runtime\g2-r471-active-war-power-fix-20260912\report.json`
(SHA-256
`F467676201497A75C08ED5F6C72AFE64618337C73EFD2BA816B981470CE1E7CD`).
The offline reclassification sidecar is `reclassification.json` beside it
(SHA-256
`D8F43EABC2A38F451FCAB1FE8DAEEB157EF8C62439B904DF96E8AFA301E924C9`)
and is GREEN. It replays no query and starts no CK3 process.

The source checkpoint and driver state remain byte-identical, cleanup is
GREEN, current round R471 is terminated, old round R470 is terminated, and the
CK3 process inventory is zero. This closes the read-only active-war strategic
power observation as a production-live primitive. It does not by itself prove
campaign dominance or choose an exit: the policy must consume the observation
alongside an owner-authored budget and a same-frame white-peace comparison.

## R471 companion certification sync

open_kaishek commit `747a0ce834417a82a06a482acb9a2d315c62dcbf`
pins the R471 root commit, original report, GREEN reclassification, corrected
runner/test hashes, native sources, and production DLL. Its focused offline
Maven test passes `4/4`. The profile marks this exact-build read-only query
native/runtime certified while explicitly keeping campaign dominance, exit
recommendation, action readiness, and GEN-034 outside that certification.
