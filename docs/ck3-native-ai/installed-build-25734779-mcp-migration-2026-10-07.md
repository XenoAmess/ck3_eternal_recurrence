# Installed Steam build 25734779: MCP migration

The user requested on October 7 Asia/Shanghai that the current work reach a suitable checkpoint, local CK3 be updated, and the project's MCP be adapted. CK3 remains minimized during subsequent game work. This is a development migration, not a workshop release.

## Saved campaign and old work checkpoint

R0051 used the original ordinary Robert 29829 campaign. The committed army route to province 2618 passed a fresh contact-horizon query, advanced exactly one day, and was independently observed paused at date `53288256`. The normal checkpoint is **h9613 / 5997 saved normal days / October 7 +1 / cumulative resume 2844 / natural successions 0**. Army 218104048 remains moving from 2619 toward 2618; no arrival, battle, victory, or full campaign completion is claimed. This is a bounded production-live route loop.

- Save: `C:/codex-ck3-background/normal-robert-saves/r0051/h9613/xar_checkpoint.ck3`, 104697984 bytes, SHA-256 `afab727d1317dbc767303a13fbf2b25916de64df182e827e24bcb2fb32062312`.
- [Actual save and independent observation](Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/managed-runtime-next-g104-h9596/ROOT-ACTUAL-FIRST-SAVED-DAY-R0051.json).
- [Complete ten-stream freeze](Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/managed-runtime-next-g104-h9596/ROOT-H9613-NORMAL-CLOSE-TEN-STREAM-FREEZE.json). The full driver was copied after normal SDK `exit_client`; its process is absent and stderr is empty. The retained tool session expired before its precise exit code could be recovered; no SDK exit-zero claim is made.
- [Owned stop](Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/managed-runtime-next-g104-h9596/ROOT-R0051-ACTUAL-AFTER-STOP-STATUS.json): owned Operator job exited 0; runner shutdown records `cleanup_proven=true`, tree gone, CK3 PID 155556 absent, and CK3 stop exit code 1. This is the managed stop result, not an unobserved normal CK3 exit-zero assertion.

The old g105 build finished rather than being interrupted: source `97a2a77da0359ceb1215e1ee8ce57831cda5f531`, 64 jobs, `/W4 /WX`, **RED exit 1 / 2881.381731 seconds**. `ordinary_holy_war_cb_cost_v1.cpp:30` reported C4324 implicit alignment padding in local `Scope`, promoted to C2220. The original [build result](C:/codex-ck3-background/joint-three-source-batch/strict01/BUILD-RESULT.json) and complete log remain retained. A minimal source fix is assigned; old-build FIRST is not resumed for migration. The g106 source batch is adopted at `0597bddcd6bea7d441efe2ce6546106953f05c22`; its new native FIRST remains NOTRUN.

## Actual installed update

Steam was switched online after the owned CK3 process was gone. Steam's content log records the app update committing four files and finishing build **25734779** at **2026-10-07 01:26:40 Asia/Shanghai**. The app manifest reports fully installed (`StateFlags=4`), update result 0 and no pending target build. Workshop auto-updates are separate log entries; their byte totals are not the game executable update size.

The new executable and complete binaries directory were frozen once at `Z:/ck3_mod_rewrite/artifacts/migrations/2026-10-07/installed-build/`. Installed CK3 is `Z:/SteamLibrary/steamapps/common/Crusader Kings III`.

| Identity | Previous installed build | Updated installed build |
| --- | --- | --- |
| Steam build | 25652598 | 25734779 |
| EXE SHA-256 | `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6` | `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` |
| New EXE size | — | 101040248 bytes |
| Game semantic version | 1.20.0.3 | 1.20.0.4, native ASCII in the new EXE |

[Frozen installed identity](Z:/ck3_mod_rewrite/artifacts/migrations/2026-10-07/installed-build/BUILD-FREEZE.json) and [Steam app update log](Z:/ck3_mod_rewrite/artifacts/migrations/2026-10-07/installed-build/STEAM-CONTENT-UPDATE-TAIL.log) are the source of this table. Windows FileVersion/ProductVersion strings are null; fixed resource words identify 1.0.0.0 and do not establish CK3's semantic version.

The subsequent [new PE metadata](Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/global-pe-diff/NEW-PE-METADATA.json) identifies native ASCII `1.20.0.4` beside CK3/Crozier at file offset71866624, RVA71871232. The shared old/new comparison read each EXE once without repeating its SHA. Both `.text` and `.rdata` change; this is not a signature-only replacement. Fixed-offset differing-byte counts do not establish semantic differences or a usable RVA mapping. Concrete function/global relocation and required field/call changes remain the next work.

## Migration in progress

The shared old/new PE comparison is owned by the Army lane, with one cached section/code/layout difference ledger for all domains. Unchanged complete regions may justify existing ABI reuse. Changed targets require exact new-build source closure before invoking them. No new RVA, patch version or ABI equivalence is inferred solely from the new SHA.

Parallel domains cover core native profile/bootstrap and SDK/Operator, Army/rules/query transport, daily/monthly supply and Unit/disembark, commander/roll, current combat and warscore membership, reinforcement/contact routes, realm/law/opinion/dread, prisoner release/ransom, family/heir/fertility, religion/tenet/doctrine/reform, holy-war context/cost, and holy-order/mercenary reinforcement. Source candidates and earlier qualification remain separate from the installed-runtime migration.

Next: use the shared actual PE delta and confirmed 1.20.0.4 version to close concrete relocation; implement the smallest supported build/profile/schema changes; compile and run only required new migration checks; restore the preserved ordinary campaign in a fresh managed run and verify paused native observations through the registered MCP. The existing giant Army text/structured duplication has a separate actual-entry performance fix and one new SDK consumer case; measured results will be recorded separately.

Current readiness is **research / updated install frozen / MCP port in progress**. There is no new-build fixture-live or production-live claim yet. The preserved 5997 campaign days are historical runtime evidence, not new-build qualification.


## Source adoption at 2026-10-06T18:22:00.751717+00:00

Event sources and offline MCP consumers are migrated to .4 at adopted f49c56fe:193 authored rows reused under unchanged depot manifest, current .3 overrides retained, and new .4 provenance/digest generated. Its one new production compound passed; see [event migration](vanilla-event-source-migration-12004.md). Active law Python profile transport is adopted42f0b2ea; new native qualification remains pending. See [active-law migration](realm-law-active-query-12004-migration.md). Root ran no old cases.

Steam was directly observed offline in fresh restored window008; no new game has launched. The official native-session lifecycle keeps the process/pipe alive without complete Snapshot readiness, so the core-only first observation can use the existing owned route. Full Snapshot and domain migration still continue. These source changes do not confer new-build production-live qualification.
