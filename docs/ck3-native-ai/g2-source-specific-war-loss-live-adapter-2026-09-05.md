# G2 source-specific war-loss concrete live adapter

Status: **R441 bounded live / R440 blocker fix live-validated / hash-bound resume admission static-ready / source capture pending**.

## Delivered platform composition

`run_g2_source_specific_war_loss_live_adapter.py` supplies the concrete
Windows/CK3 operations required by the previously frozen exclusive outer
owner. One invocation now has one process owner and one ordered lifecycle:

1. acquire the repository CK3 exclusive-launch lock and require an empty CK3
   process inventory;
2. launch the exact `1.19.0.6` executable normally into a fresh isolated
   `-userdir`;
3. attach the frozen private source observer to that PID, select natural
   `bookmark.1071.a` at speed 5, require six typed source executions, restore
   the breakpoint byte and detach without killing CK3;
4. prove the same owned PID remains alive and pause it through rendered UI;
5. inject the frozen bridge DLL with an explicit unique pipe into that PID,
   then require the bridge-reported PID, paused state, map readiness, played
   character and episode identity;
6. hand the exact driver object to the existing same-lifecycle current → one
   surrender → destroyed cleanup → persisted-expiry continuation;
7. close the driver, terminate only the owned observer/CK3 processes, prove
   CK3 inventory empty, and release the outer lock exactly once.

If process discovery fails after `Popen` but before the launch receipt reaches
the outer owner, the adapter now performs exact-PID emergency reclamation
itself. That closes the only interval in which the outer owner could not yet
own cleanup.

This runner is Python orchestration, not a CK3 effect owner. It does not alter
the project's mandatory purpose-sharded effect layout or its `1..10`, hard
`<=20` boundary.

## OCR and native-state boundary

OCR is still used only where MCP cannot exist yet: main-menu readiness,
Robert bookmark selection, the naturally scheduled event popup, and rendered
pause confirmation before bridge injection. OCR does **not** establish any
source, WarID, generation, soldier, action, cleanup, expiry or readiness fact.

- source attribution truth comes from the exact-build private native observer;
- current/action/postwar truth comes from the same-PID native MCP driver;
- no screenshot or OCR string may promote `source_specific_loss_ready`.

The natural-event definition is frozen by exact `bookmark_events.txt`
SHA-256
`75CF485E379E522D4AAED9EF889FCC411A0D9DFCC28BCFB250ABDCC93A757EFF`.
Its initial game-start schedule is a random `years={1 7}` and a failed trigger
may reschedule by 25 days, so the event date cannot be authored into the
command. The adapter instead freezes `expected_date_raw` from the first
same-PID paused bridge snapshot and passes that exact value into the current
double-query contract.

## Frozen command and no-launch evidence

The manifest
`native_bridge/research/fixtures/g2_source_specific_war_loss_live_adapter_v1_manifest.json`
pins the adapter and every executable/source dependency. Important hashes:

| Input | SHA-256 |
| --- | --- |
| adapter | `94E179F41D9BAB852D9A8E5CB50D9D1E7ED9C69F792C4650E93B626BE267E9F7` |
| manifest | `056D765A29707D206432973960E4863D011C6132ECB5C87F97C72D0A7A4AAA9A` |
| source capture executable | `B8328D5C0B52AF667BB71D2BBE660C803BF46EC0A7549A514083B7DBB8BA5A72` |
| bridge DLL | `4D839524098891BD997009663E189929722746AB0404D88C1E91F7546EFE238B` |
| bridge injector | `43983E28CE3FBFC5EA1F26786834AD5E9133E59807BDCB18FB244BA8E830E08D` |
| CK3 executable | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |

The no-launch command is:

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" -B `
  "ck3_autonomous_player\native_bridge\research\run_g2_source_specific_war_loss_live_adapter.py" `
  --manifest "ck3_autonomous_player\native_bridge\research\fixtures\g2_source_specific_war_loss_live_adapter_v1_manifest.json" `
  --preflight-output "<fresh-output>" `
  --profile-settings-template "<known-good-profile>\pdx_settings.txt" `
  --game-root "<CK3-install-root>" `
  --expected-war-id 50331699 `
  --verify-only
```

It produced
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-source-live-adapter-static-20260905\preflight-r3.json`,
7,061 bytes, SHA-256
`F0A5943228422B3E7E5F2B734BE7CD35B12E76C391F048BABC1D2448FA31C471`.
Status is `READY_TO_RUN_G2_SOURCE_SPECIFIC_LIFECYCLE`; before/after process
inventories were identical and included PID `98608`, the root thread's
already-running exclusive Phase2 CK3 process. This command neither started,
attached to nor terminated that process; it is occupancy evidence, not G2
live evidence.

### 2026-09-06 current-main revalidation

The same `--verify-only` command was rerun from `master@74a2cb2` after the
Phase2 copy-audit merge. It again returned
`READY_TO_RUN_G2_SOURCE_SPECIFIC_LIFECYCLE`; every manifest-pinned source,
runner, DLL, injector, capture executable, game executable and bookmark hash
matched. The before/after process inventories were byte-for-byte equal. No
CK3 process was started, attached, focused, injected into or terminated.

The fresh receipt is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-source-live-adapter-static-20260906\preflight-current-master-r1.json`,
6,691 bytes, SHA-256
`59392C6E7ED3612B34BEAD6DD9C145D61A261747610831F2D99EC29211BC6F38`.
This only proves that the already frozen live command remains executable from
the current integration head. It does not promote source-specific loss,
comparison, decision, action or `GEN-034` readiness.

### 2026-09-07 post-`1f5e310` no-launch refresh

After the source-contract hash repair landed at `1f5e310`, the same
`--verify-only` entry was rerun from `master@5ffbc1d`. The report is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-source-live-adapter-static-20260907\preflight-master-5ffbc1d-r4.json`,
7,067 bytes, SHA-256
`6BB2090ADEB83D99906F5D88682CF602A69BD48E14EAA12F98C4F2592EA2CCC6`.
It returned `READY_TO_RUN_G2_SOURCE_SPECIFIC_LIFECYCLE` and bound the current
manifest SHA-256
`D888FA2DF6839C5A424D9947EE7BCE746ABF930E45B2384169DD23488ABB5FB0`.

The before/after process inventories were identical and retained the already
running CK3 PID `44264`; this command did not start, attach to, focus, inject
into or terminate CK3. The occupied process is proof that a later live run
still requires an exclusive empty slot, not source-specific live evidence.

No additional offline implementation can remove the remaining decision gate:
the campaign and white-peace utility producers still require production/owner
inputs. The typed `surrender-war-N` submit and private postwar receipt already
exist in the frozen lifecycle runner; promoting that submit into the public
policy before production recommendation, pending/cooldown and full
postconditions are available would not unlock an authorized decision.

### 2026-09-09 isolated-worktree game source binding

The adapter now accepts an explicit `--game-root` for a CK3 installation that
contains `binaries/ck3.exe` and `game/events/bookmark_events.txt`. Callers may
instead provide either file independently through `--game-executable` and
`--bookmark-events`; a direct file argument takes precedence over
`--game-root`. These options change only path resolution. Every selected file
must still match the SHA-256 frozen in the manifest, and `ck3.exe` must also
match the exact `1.19.0.6` executable identity.

A no-launch run from isolated worktree
`_root-rebase-r345-20260909@2121dc6` used
`--game-root "Z:\ck3_mod_rewrite\Crusader Kings III"` and returned
`READY_TO_RUN_G2_SOURCE_SPECIFIC_LIFECYCLE`. All 14 manifest dependencies
matched; the executable and bookmark rows record
`path_source=explicit-game-root`, and the report records
`exact_hashes_verified=true`. Process inventory was identical before and
after, including the CK3 process already owned by the concurrent T0 run; this
command did not start, attach, focus, inject into, stop or mutate that process.

Receipt:
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-explicit-game-path-no-launch-20260909\preflight-origin-master-2121dc6.json`,
8,291 bytes, SHA-256
`11B66665FDE1F095CCD72C47B9D4B8A987AD87E2A3B27E3F099D7D821CC73233`.
This closes only the isolated-worktree preflight path gap; all live/readiness
fields remain unchanged.

### Relocatable runtime binaries

The adapter also accepts explicit `--capture-executable`, `--bridge-dll`, and
`--bridge-injector` paths. These arguments let another operator or machine use
a byte-identical frozen runtime bundle without editing the manifest's local
default paths. An explicit path takes precedence only for its named dependency;
the manifest remains the source of the expected SHA-256, and a relocated file
with different bytes is rejected before any launch or attachment.

Omitting all three arguments preserves the original manifest-path behavior.
The no-launch test matrix covers explicit-path precedence, a fully relocated
fake bundle, hash-drift rejection, default fallback, and CLI forwarding. This
is a launch-wrapper portability change only: it does not alter the native
bridge or MCP schema/API, create production evidence, or advance any G2
readiness field.

After the coordinator grants an exclusive CK3 slot, the concrete default-OFF
command is:

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" -B `
  "ck3_autonomous_player\native_bridge\research\run_g2_source_specific_war_loss_live_adapter.py" `
  --manifest "ck3_autonomous_player\native_bridge\research\fixtures\g2_source_specific_war_loss_live_adapter_v1_manifest.json" `
  --preflight-output "<fresh-attempt>\preflight.json" `
  --artifact-dir "<fresh-attempt>\artifacts" `
  --userdir "<fresh-empty-userdir>" `
  --profile-settings-template "<known-good-profile>\pdx_settings.txt" `
  --game-root "<CK3-install-root>" `
  --capture-executable "<runtime-bundle>\xar_ck3_raiktor_war_bound_private_capture_v1.exe" `
  --bridge-dll "<runtime-bundle>\xar_ck3_bridge.dll" `
  --bridge-injector "<runtime-bundle>\xar_ck3_bridge_injector.exe" `
  --expected-character-id 29829 `
  --expected-war-id 50331699 `
  --postwar-timeout 45 `
  --authorize-private-live
```

Without `--authorize-private-live`, the command stops after no-launch
preflight. Artifact and userdir paths must be fresh. A RED attempt must be
preserved and must end with the same owned-process cleanup proof.

### 2026-09-10 portable operator MCP no-launch entry

The adapter's explicit game/runtime path overrides are now consumed by a
generic profile generator. Each operator or machine supplies its own target
identity, endpoint, clone and byte-identical runtime paths; the generated
operator profile hash-binds every input and exposes only this adapter's
`--verify-only` command. It contains no live authorization, artifact/userdir,
stdin control, account constant, host-root constant or fixed CK3 round.

See
[the G2 operator MCP no-launch profile record](g2-source-specific-operator-mcp-preflight-2026-09-10.md).
This closes deployment assembly only. No live lifecycle was run and all G2
source-specific/readiness boundaries remain unchanged.

## Verification and remaining boundary

The adapter suite is GREEN in normal and optimized Python. The combined
source-provider/outer-owner/lifecycle/postwar focused matrix is GREEN in both
modes; no CK3 was launched for this package.

Until a qualifying exclusive live run succeeds,
`source_specific_loss_ready=false` and `comparison_input_ready=false`. Even a
successful run changes only those two inputs. Three-way choice remains blocked
on `campaign-dominance-certificate`, `owner-authored-budget-profile`, and
`same-frame-white-peace-comparison-certificate`; decision/action/automatic
surrender and `GEN-034` remain false. T1 therefore remains **90%**.

### 2026-09-11 current-checkout admission refresh

The first current-checkout no-launch attempt stopped before CK3 because the
manifest still pinned the whole-file SHA-256 of
`tools/run_zg361_phase2_seed_capture.py` from the original adapter package.
Later Phase2 work changed unrelated portions of that large module. A direct
AST comparison against `7dec66d` confirmed that all seven definitions consumed
by this adapter remain identical: `SeedCaptureError`, `sha256_file`,
`tree_manifest`, `_settings_file_is_full`, `_warm_shadercache_manifest`,
`_profile_startup_assets_error`, and `prepare_profile_settings`.

Only the stale whole-file hash was refreshed. The adapter, outer owner,
lifecycle runner, native binaries, exact game files, source provider and source
contract remain byte-identical to their frozen values. The replacement
manifest SHA-256 is
`4A370EEAE10B588ABD6730D2F4E0FC0998A73D80ADECE1A8CF778F2F54D73079`.

The second no-launch attempt returned
`READY_TO_RUN_G2_SOURCE_SPECIFIC_LIFECYCLE`. Its receipt is
`Z:\ck3_mod_rewrite\_runtime\g2-source-specific-r440-20260911\preflight-green.json`,
20,184 bytes, SHA-256
`81A9F1D38FF1ED1F86FC89652A3D268D9F1ADCC336FFCE91ED5C729CEDCFAE4C`.
The source settings/cache pair is ready (`4,956` files, `216,470,121` bytes),
the CK3 inventories before and after are identical, and no CK3 process was
started. The directory name reserves the intended next live round; this
preflight did not create R440. Live/readiness values remain unchanged until the
exclusive command succeeds.

### R440 encountered blocker and bounded repair

R440 launched one CK3 1.19.0.6 process, PID `182552`, from the admitted
manifest. It reached Robert 1066, handled `bookmark.1070.c`, and advanced at
speed 5 until the stock single-option event `埃玛成年` paused the map. The old
fallback sent `Shift+1`; twenty-two bounded attempts left the same event open.
The representative screenshot is
`live-artifacts/ui/bargain_g2-post-blocker-4_speed_5_stalled.png`. The frozen
R440 RED receipt is
`Z:\ck3_mod_rewrite\_runtime\g2-source-specific-r440-20260911\r440-harness-red.json`,
2,426 bytes, SHA-256
`4016A49E72071DCA176224C5AE1283DBBC2293685F384EDB00023DFE7520B441`.

The run was stopped once the repeated action supplied no new information.
PTY interrupt bytes did not reach the Python child, so cleanup targeted the
recorded driver, observer and CK3 PIDs; all exited and the final CK3 inventory
was empty. R440 never selected `bookmark.1071.a`, captured source executions,
injected the bridge or submitted surrender. This is harness RED and does not
change G2 product readiness.

The adapter now calls the established `quick_stall_and_recover` path. It clicks
only an OCR-ranked event option whose disappearance is verified and returns RED
when no verified option exists; the blind keyboard fallback is removed. Offline
replay of the R440 screenshot selected the classic option at `[930, 1043]`.
Focused adapter tests pass `20/20` in normal and optimized Python. Both changed
Python files now satisfy the repository UTF-8 BOM rule, and the final no-launch
preflight returns `READY_TO_RUN_G2_SOURCE_SPECIFIC_LIFECYCLE`. Final adapter and
manifest SHA-256 values are
`CE9FF6D910D68003EA2768AA28E4B4871595FE648EB9EDDA3CCFECC9C4224848`
and `29549DFC108DFB734A3FB38D2AF00DE3C042DD928E71E9324F1FAD1C0B4113DE`.

### R441 bounded retry and preserved continuation

R441 launched the exact build once as PID `140912` from root commit
`a911c253ec29d3de1b204d4e4b91780e3a81e891`. It reached the map and ran only
the manifest's existing 520-second target window. The repaired recovery path
closed 18 stock events with a verified OCR option and verified time resumed
after each one; one modal also required the existing verified timeline-play
recovery. This is sufficient live evidence for the R440 blocker repair.

`bookmark.1071.a` did not appear before the bounded deadline. No source capture,
bridge injection or surrender occurred, so source-specific readiness remains
false and T1 remains 90%. This is a target-event precondition/scheduling miss,
not a product RED. The exact-build definition schedules `bookmark.1071` at
`years={1 7}`, requires `gold >= 100`, `is_at_war = no`, and a Byzantine holder
other than root, then retries after 25 days while that holder condition remains.
A durable R441 frame at game date `1073-10-31` shows 694 gold, proving that the
run had already crossed the latest initial scheduling boundary; simply extending
the same attempt would therefore be the wrong response.

The frozen receipt is
`Z:\\ck3_mod_rewrite\\_runtime\\g2-source-specific-r441-20260911\\r441-bounded-attempt.json`,
3,716 bytes, SHA-256
`E8EE575557FA9D4CF90055FB8B4DC540100E7CCA5867E199594789E038EDF88F`.
The runner report is 2,979 bytes, SHA-256
`FDE8FB0AC7A1A269FF238DFD75E4F02F501A4227928ED6B34E92D5024291B128`;
its cleanup is GREEN and the final CK3 and driver inventories are both empty.
The preserved `last_save.ck3` is 85,561,556 bytes, SHA-256
`A0E122CAFA2A89C418C0A641A08A980DD880299E05561B7B6887508E9A351A98`.
It is only a resume candidate until a hash-bound copy/load admission validates
it. The next implementation package must consume that checkpoint in a fresh
userdir instead of replaying the completed prefix or enlarging one live window.

### Hash-bound R441 continuation admission

The adapter now accepts the optional all-or-none pair `--resume-save` and
`--resume-save-sha256`. Before any launch, it requires a non-empty `SAV0101`
save whose header contains exact game version `1.19.0.6`, then verifies the
declared SHA-256. A live invocation copies the admitted bytes to
`<fresh-userdir>/save games/autosave.ck3` and rechecks both size and SHA-256
before `Popen`. The launch receipt retains `startup_mode=normal-event` for the
outer-owner contract and records `startup_source=resume-checkpoint`; omission
of both arguments retains the original new-game route.

The resume UI route selects the visible `继续游戏` entry once, after which the
existing map/event/source lifecycle owns the run. It does not trust OCR for
save identity or any source-specific fact. The selected source and copied
destination are both recorded in `resume-checkpoint.json` and in the final
report.

Focused verification is GREEN: adapter tests are `23/23` in normal Python and
`23/23` under `-O`; outer-owner compatibility tests are `8/8` in both modes;
`py_compile` and the UTF-8 BOM checks pass. A real no-launch admission consumed
the R441 candidate and returned
`READY_TO_RUN_G2_SOURCE_SPECIFIC_LIFECYCLE` without creating a CK3 process. Its
receipt is
`Z:\ck3_mod_rewrite\_runtime\g2-source-specific-resume-admission-20260911\preflight-final.json`,
20,613 bytes, SHA-256
`1D5B0B773897A8975369D605272D2638D2C00E38F263F4EA8EC8074C7F9CB88B`.
It binds the 85,561,556-byte source at
`A0E122CAFA2A89C418C0A641A08A980DD880299E05561B7B6887508E9A351A98`,
reports game version `1.19.0.6`, and leaves the before/after CK3 inventories
identical and empty.

The resulting adapter SHA-256 is
`13202ADABC42D0A777EA22B946B9988CC9A9B287AAAF16C3D80C97CBDAAAB33C`;
the manifest SHA-256 is
`A2C2A93F08E23074D18B3181D7CF6C4ADDA5635C9B5E609BD736333564D59763`.
This package is static-ready only. It does not promote source-specific loss,
comparison, decision, action, automatic surrender or `GEN-034`; T1 remains
90%. Current round R441 is ended and CK3 inventory is zero. The next bounded
live action is one fresh-userdir continuation from this exact checkpoint.
