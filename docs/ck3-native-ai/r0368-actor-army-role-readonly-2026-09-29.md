# R0368 actor army role: paused read-only interface boundary

## Observed state

The R0368 source request concerns actor `29829` in episode
`native-29829-2bc2d599f7f9` at date raw `53219928`. The activity planner
reported `activity_feast` Stage 5 `final_can_start=false` and a localized
commander-or-knight failure, with zero selected nonhost guests and no Start.
The source's 2026-09-29 correction says that this R0368 process has ended and
its report contains **no typed army-role row**. The current role and any safe
release boundary are therefore unknown. The corrected report SHA-256 is
`883CC43B513CE7F01A18A61DB27ACCA923F2F3D781F5836306AC0B7FCEE39EB6`;
the first request omitted two hex characters in that value.

An earlier, distinct H3928 `query-combat-simulation-inputs-v3` row observed
public ArmyID `83886367`, native CArmyID `50331794`, owner `29829`, current
province `2610`, and commander `29829`; the actor was absent from that row's
14 knight members. This is historical evidence from another native query.
Matching episode and date fields do not make it a role observation in the
R0368 paused frame. Its fixed WAR excerpt is
`R0345-H3928-WAR-SIEGE-FORECAST-RED/SOURCE-R0345-H3928-V3-RAW-EXCERPT-v1.json`,
SHA-256 `C91DDA8284E414D96FA7705AA0881A048CF0CAB2F83AB4817F7826F5C5A63F67`.

## Existing native source

The public `player_armies` snapshot and private
`query-m5-war-primary-current-v1-...` expose ArmyID, owner, province and
route, but no actor commander/knight assignment. The battle-control selected
commander and knight fields describe a bound active combat, so they do not
answer an ordinary raised-army role question. The existing V3 hypothetical
combat-input command can expose a selected army's native commander and knight
members; it also requires a contact scenario and its completeness belongs to
that hypothetical query. It must not be used as a general role or war-action
gate.

The verified CK3 `1.19.0.6` anchors already used by the combat adapter are:

| Field | Existing source and check |
| --- | --- |
| Public and native army identity | `CUnit+0x178` CArmyID, `CArmy+0x10` exact ID, `CArmy+0x124` reverse CUnit ID, `CUnit+0x174` owner; see `prewar_scope_v1.cpp` `ReadOneSample`. |
| Commander | `CArmy+0x120` full CharacterID, `-1` absent; resolve exact `CCharacter+0x18` and compare the native `get_army_commander` helper; see `ck3_11906.cpp` `ReadCombatCommander`. |
| Knight | Complete `CArmy+0x38/+0x40/+0x44` regiment ID array; each exact CRegiment's `+0x140` army link and `+0x148` CharacterID, checked against `CCharacter+0x1B0` link whose `+0xF8` is the regiment ID; see `ck3_11906.cpp` `ReadCombatKnights`. |
| Army state | Current/target province, route, retreat and combat IDs have separate native sources; the current H3937 R0271 work is still resolving battle/siege participant coverage. A role query cannot promote these fields into a safe role-release decision. |

## Minimal future private query

Candidate step: `query-war-actor-army-role-v1-<actor-character-id>-<war-id>-<public-army-id>`.
Keep it disabled until its own static and exact paused live acceptance. It is
an independent query; it does not change H3937 phase-0 or the R0271 date gate.

1. Require paused and map-ready state, exact played actor and positive canonical
   IDs, a single native revision, and before/after snapshot identity, date and
   connection generation equality. Reject an unbound episode or changed save.
2. Resolve the requested public CUnit and native CArmy with both ID/backlink
   checks. Return public ArmyID, native CArmyID, owner, province and typed army
   state with a source/revision tag. Compare those fields to the same-frame
   public `player_armies` row. A missing or contradictory row is `unavailable`.
3. Read the commander ID through `CArmy+0x120`, validate the character pointer
   and native helper, and report `is_commander_of_requested_army` as true or
   false only if this chain is complete. A failure is `unknown`, never false.
4. Traverse the entire bounded regiment array, resolve every CRegiment and
   validate each army and character reverse link. Report
   `is_knight_in_requested_army` as true or false only after the entire array
   is complete. Include matching regiment ID when true. A partial array or
   generation change is `unknown`, never false.
5. Limit negative claims to **this requested army**. Establishing that the
   actor has no role in any army needs separate complete live-army enumeration
   or a verified character-level reverse index. If that proof is absent, return
   `global_commander_or_knight_status=unknown` even when both requested-army
   flags are false. Preserve the raw activity CanStart read as a separate
   source; do not derive role identity from translated failure text.
6. The command returns no release action, role mutator, activity Start, date
   advance or changed war policy. Return typed `unavailable_stage` for failed
   identities, unsupported game versions, stale frames and missing bindings.

## Implemented private candidate

The implementation lives behind the CMake option
`XAR_CK3_ENABLE_WAR_ACTOR_ARMY_ROLE_PRIVATE_V1=ON`; the default is `OFF`.
It adds no public capability and uses the paused application-main query
mailbox. Its native step is
`query-war-actor-army-role-v1-29829-16777231-83886367`. The Python entry point is
`NativeCK3Driver.query_actor_army_role_private_v1` with explicit
`allow_private_actor_army_role_query=True`, actor ID, WarID, public ArmyID,
episode run ID and expected revision. The default Python flag is false and rejects before
sending a command.

The result contains `actor_army_role.status` (`available`, `partial` or
`unavailable`), exact source revision/date and actor/public/native army IDs,
public army state, typed commander and knight assignment for the requested
army, and a reason for any missing domain. The global role field remains
`unknown`, safe release is null, and date credit is false. A missing member in
an incomplete regiment array is never reported as false. The Python transport
requires the before/after paused snapshot binding and refuses extra or
changed result fields. The C++ reader checks public/native ArmyID backlinks,
owner/province, every regiment's army and knight reverse links, and a native
commander-helper agreement. Its application-main collector reads only; it
does not submit a role, army, war, activity or date action.

The initial source candidate `bb748c4fe0440aad4059d5e5b5495db68308d225`
and fixed WAR response v4 are historical **RED** candidates: the collector
did not double-read native roles or freeze all storage and regiment headers,
and the Python side did not bind episode, WarID or connection generation.
The corrected source requires one exact allied ArmyID in the requested war,
an exact native expected revision, two identical complete native role samples,
unchanged four storage headers and regiment-array header, unique regiment IDs,
valid character predicates and a known current province whose pointer matches
the game state's canonical province array. Any drift returns a
typed unavailable or partial result without a false role assignment. The
native source gate fixture mutates each header and sampled field, and the
Python tests exercise episode, war, army membership, connection, event and
capability drift under normal and optimized Python.

## Release build and offline acceptance

The corrected candidate is at `7457ef060cdfa1c943c86be619df02dbbb247dd0`.
Its only change after the independent source review at `4996e2763` replaces
a fixture's MSVC-invalid `-1ULL` with the explicit maximum `uint64_t` value.
The same `/W4 /WX` fixture compiles and runs independently. Earlier build
attempts remain separate: 001 and 002 were resource/performance interruptions;
003 failed at that C4146 fixture warning; 004 linked all 915 targets but
its default, nonexistent worktree `ck3.exe` made 16/173 CTest cases fail.
Those attempts are not upgraded to GREEN.

Fresh Release [attempt 005](D:/ck3-research-artifacts/r0368-role-release-pair-attempt-005.json)
pins the installed CK3 `1.19.0.6` executable at
`C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`,
SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The default-off private option is explicitly ON for this isolated build.
All 915/915 targets linked; the build script's dependency-record gate passed;
offline CTest passed 173/173, including
`xar_ck3_actor_army_role_source_gate_v1`. A separate
[JUnit XML](D:/ck3-research-artifacts/r0368-role-ctest-junit-005.xml)
run also passed 173/173 with zero failures or skips. The frozen
[pair manifest](D:/ck3-research-artifacts/r0368-role-release-pair-attempt-005.json)
has SHA-256 `798A3E8ADC055C39B170D2F37F2BC2074A7994882D078DFDACB74C73CF71149C`;
the [build log](D:/ck3-research-artifacts/r0368-role-build-stdout-005.log)
has SHA-256 `EC4390F728508D910CBB74507BE5A5758C4039111BF61062CDA061D784163BBA`,
and JUnit XML has SHA-256
`873FB98E4CA4BB4012FEC244E5061349F5714842B22A91007A15B870567DE368`.
The paired Release DLL is 3,148,800 bytes, SHA-256
`F360FA9F55F1628A03CE111458983A67E769BB9E78BA85EA202CB819BA805425`;
the same-directory injector is 39,936 bytes, SHA-256
`6EB871817A6861F431DB50759B2EC607B80E0DAE269A8B1B2610F98212355C01`.
No CK3 process was started or screen acquired for these offline checks.

`open_kaishek` has no deterministic parser/IR/runtime subset for this exact
native memory-pointer, storage-header, commander-helper and regiment-link ABI;
its configured `Z:/workspace/open_kaishek` path is also inaccessible here.
The C++ source gate and offline CTest suite are the applicable prevalidation.
This is static build acceptance only. No typed paused-frame role row exists,
and the completed R0368 report cannot be retroactively upgraded.

## Later no-launch source candidate

The H3937 R3944 attempt-09 source checkpoint and driver share the actor,
episode and date anchors needed for a *future* read, but its existing DLL
does not contain the R0368 role command. A separate
[R0368 candidate manifest](D:/ck3-research-artifacts/r0368-role-no-launch-20260929/attempt-01/candidate-manifest.json)
(SHA-256 `1F0BB07ED5FABF89EA8E82CE8CC178388F22DC8BB35590AA045846E06FE89E25`)
preserves byte-checked copies of that checkpoint, driver and sidecar together
with the new paired role DLL and injector. Its read-only
[no-launch preflight](D:/ck3-research-artifacts/r0368-role-no-launch-20260929/attempt-01/preflight.json)
(SHA-256 `8887294905B0E775C4C8B60C6CD3692FF4F809213BFD3A0B8171093778E1DDAF`)
checks the copied bytes, exact EXE and unchanged native source. It neither
starts CK3 nor enables an operator. The driver file has no current paused
public/allied army row or native revision; therefore WarID `16777231` and
public ArmyID `83886367` remain candidate inputs, not same-frame facts.
Any live query needs a new paused semantic snapshot and separate fresh
screen/offline admission.

The release decision is a later war-policy step. It needs the exact current
assignment, a complete army and contact/siege state, a valid replacement plan,
and a qualified nonwar benefit. R0271 remains RED, so this interface gives no
date or role-release credit. Its first live use requires a new exact paused
attempt and separate screen/offline admission; the ended R0368 frame cannot be
retroactively upgraded.
