# open_kaishek acceptance coverage

This matrix records the one-time source audit performed on 2026-09-02.  The
offline gate is an accelerator only; it never upgrades a run to CK3 live,
paused-snapshot, MCP, or production readiness.

| Entry point | CK3/desktop boundary | Offline decision | Hook and evidence |
| --- | --- | --- | --- |
| `tools/run_acceptance.py` | Base XAR debug/live runner | Parser + validator over `XenoAmess_s_Eternal_Recurrence`, fixture `none` | Direct call at the start of `preflight()`; result is retained in `report.json` |
| `tools/run_terminal_acceptance.py` | Non-debug observer/Ironman wrapper | Reuses the base XAR gate; no second invocation | Delegates to `run_acceptance.main()`; the base call runs before launch |
| `tools/run_vivhite_acceptance.py` | Vivhite standalone/dual matrix | Parser + validator over the checked-in `vivhite_acceptance` fixture, fixture `none` | Direct call at the start of `preflight()`; result is included in cell and matrix reports |
| `tools/run_ox_here_acceptance.py` | Ox Here non-debug cell | Parser + validator over the checked-in `ox_here_acceptance` fixture, fixture `none` | Direct call at the start of `preflight()`; result is included in the cell report |
| `tools/run_zhongguo_acceptance.py` | ZhongGuo 361 native/MCP and promo modes | `ck3-1.19.0.6-zg361` profile with the configured runtime root and `synthetic-361-014` | Existing direct adapter call at the start of `preflight()`; result is copied to `open_kaishek-preflight.json` |
| `tools/run_zg361_phase2_seed_capture.py` | Direct phase-two native-session/CK3 seed capture | `ck3-1.19.0.6-zg361` over the frozen product root plus `synthetic-361-014` | Direct adapter call in both no-launch `run_preflight()` and capture `run_capture()`; the latter runs before supervisor startup and writes `open_kaishek-preflight.json` |
| `tools/run_ox_here_loc_smoke.py` | Fresh-process CK3 localization matrix (desktop + launch per language) | Parser + validator over the checked-in `ox_here_loc_smoke` fixture, fixture `none` | Direct call at the start of `preflight()`; result is included in the matrix report |
| `ck3_autonomous_player/native_bridge/research/run_*_live_acceptance.py` | Native bridge/save/checkpoint live probes | Not applicable for the current profile: these steps exercise native save/bridge semantics, for which the current offline profile has no deterministic source/fixture subset | Keep the live boundary and evidence requirements unchanged; do not add no-op CLI calls |

The terminal wrapper does not call the adapter itself because doing so would
run the same immutable XAR corpus twice.  The wrapper's only CK3 delegation is
`run_acceptance.main()`, whose `preflight()` owns the single call.  The static
contract test `tools/test_acceptance_open_kaishek_coverage.py` checks this
ordering and the no-duplicate terminal path without starting CK3 or touching
the desktop.

For all rows, an absent checkout/JAR is recorded as
`NOT_APPLICABLE`; `FAILED`/`UNSUPPORTED` from the accelerator remains separate
from the runner's own CK3 result.  The exact command and provenance are
provided by `tools/kaishek_preflight.py` and the external
`open_kaishek.preflight.v1` contract.

The parent adapter's stable minimum contract marker is `open_kaishek`
`b306a95` (or a compatible descendant).  It does not pin a moving mainline
commit: each invocation resolves the checked-out HEAD and JAR SHA-256 and
archives both, so an already-updated `Z:\workspace\open_kaishek\main` is
used without a network fetch. An intentionally different checkout/JAR can be
bound with `XAR_OPEN_KAISHEK_ROOT`, `XAR_OPEN_KAISHEK_JAR`, and the explicit
provenance override `XAR_OPEN_KAISHEK_COMMIT`. A legacy JAR that answers
`preflight` with the generic `UNSUPPORTED` envelope remains `UNSUPPORTED`; a
missing checkout or JAR remains `NOT_APPLICABLE`.

The default subprocess timeout is 180 seconds. This replaces the former
120-second bound after a real 76-file full-corpus preflight exhausted that
window. The effective value is included in adapter provenance and can be
overridden with `XAR_KAISHEK_PREFLIGHT_TIMEOUT_SECONDS` for a specifically
bounded corpus; changing it does not alter any CK3 live timeout or evidence
level.

## Progress-report fields

Use the following compact fields in the daily and weekly reports:

| Field | Value for this audit |
| --- | --- |
| `acceptance_preflight_coverage` | `7/7 CK3/desktop entrypoints covered` (five new direct hooks, one existing ZhongGuo hook, and one terminal wrapper that inherits the base hook) |
| `acceptance_preflight_entrypoints` | `run_acceptance`, `run_terminal_acceptance`, `run_vivhite_acceptance`, `run_ox_here_acceptance`, `run_ox_here_loc_smoke`, `run_zhongguo_acceptance`, `run_zg361_phase2_seed_capture` |
| `acceptance_preflight_na` | No N/A coverage gap among the seven; native-bridge research `run_*_live_acceptance.py` remains N/A/excluded because the current profile has no deterministic source/fixture subset for its save/bridge semantics |
| `acceptance_preflight_semantics` | Offline parser/validator accelerator only; an adapter `NOT_APPLICABLE`, `UNSUPPORTED`, or `FAILED` result never becomes CK3 live/readiness evidence |
| `acceptance_preflight_evidence` | Commits `9764ad6`, `6c2117a`, `9cf958a`; coverage 4/4 and adapter 7/7; no CK3 or desktop run performed |

Copy-ready daily wording:

> `open_kaishek` source coverage is 7/7 for the CK3/desktop acceptance
> entrypoints (terminal reuses the base gate; ZhongGuo already had its gate).
> The gate is advisory and offline, so readiness/live status is unchanged;
> native-bridge research runners remain N/A for the current profile/fixture.

For the weekly report, retain the same count and boundary, then link this
matrix and the evidence commit.  Do not describe the count as CK3 gameplay
coverage, a paused snapshot, or a production-live result.

## Current accelerator provenance (2026-09-02)

The canonical accelerator is now `open_kaishek` `main` at
`a6705894bb41d87aa5e53530d77910369c6eb209`, with the rebuilt CLI JAR pinned
to SHA-256
`392B130B7F6DCB516627EAE284CF673C7F109D6857A5C6388AE56F02EC0BF1AD`.
The latest direct phase2 preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\kaishek-has-perk-preflight-20260902.json`
(SHA-256
`F37560B6C0B3113C3B6F0EDE04368E9C5B57BE55F473938DCE7A2D355787E8E9`):
parser `76/23,831,410/0` is GREEN, while the validator remains the bounded
schema-only `RED/233,014`; CK3 was not started. The short-lived schema branch
was merged and removed promptly. This evidence updates only offline
preflight provenance, not any live/readiness status.

## Current accelerator provenance (2026-09-02 09:40)

`Z:\workspace\open_kaishek` is clean on `main == origin/main` at
`757fb1b0d0b92fd234961f32e853f9cdef7069d1`. The latest exact-build-backed
schema increment is the scalar `has_dynasty_perk` descriptor; it adds profile
and validator coverage only and makes no runtime-certification claim. The
rebuilt CLI JAR is 316,162 bytes with SHA-256
`D4BA0FF5E6A9C85ED0853FD78D44940E98445F2867E9D6CA5902AF0E19B29476`.

The direct frozen-phase2 preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\kaishek-dynasty-perk-preflight-20260902-adapter.json`
(SHA-256
`37A1B6788306FD7FF8C1DFBAEDE1BE44B5B26602CE7E85334FF6A8B042A14426`).
Parser/root-scan is GREEN (`75/23,831,185/0`), fixture IR/runtime is GREEN,
and the bounded validator remains RED (`233,014`); `ck3_started=false`.
This is offline schema/fixture evidence, not CK3 live or MCP readiness.

The parent loader observer `a5c079e` consumes this preflight only as an
offline accelerator and records typed database-node context for later native
callback correlation. It does not turn parser/validator output into a CK3
live result.

## 2026-09-02 09:55 schema follow-up

The accelerator is now clean at `main == origin/main ==
7da444d6afbeb98ec6c9d91da49535a43d55d0ce`. The exact-build-backed scalar
`has_dlc_feature` descriptor is syntax/profile-only (`certified=false`); 12
profile and 22 validator tests plus offline packaging passed. The CLI JAR SHA-
256 is
`78AFD52B147874070813B5E77FA710B082065C6BB14EB3C9071A833BB0FEF2A9`.
The full parent-root preflight was parser/IR/runtime GREEN with the expected
bounded validator RED (`39,360` diagnostics), and `ck3_started=false`; its
stdout was not persisted as a separate artifact. This increment does not
change any CK3 live/readiness claim.

## 2026-09-02 10:08 G2 preflight binding

The fresh G2 native entry used the then-current clean accelerator binding
`757fb1b` / JAR SHA
`D4BA0FF5E6A9C85ED0853FD78D44940E98445F2867E9D6CA5902AF0E19B29476`.
Its archived adapter preflight is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-fresh-semantic-ready-20260902T100431236\open-kaishek-preflight-mod-20260902.json`
(SHA-256
`5F7F67C439D8721E56C735E2DFA49E07A32630DD7019EB221C1C1215DD68AC90`), with
parser/root-scan and IR/runtime GREEN, bounded validator RED, and
`ck3_started=false`. The later `7da444d` `has_dlc_feature` slice is
orthogonal schema work; it does not invalidate or require repeating that
already completed preflight. Offline output remains advisory and never
promotes CK3 readiness.

## 2026-09-02 10:24 schema follow-up

The accelerator is clean at `main == origin/main ==
bd980e787e8e64b64104b43542ae2afefe3e8a06`. The exact-build-backed
`has_court_position=<court-position-key>` scalar descriptor is
`certified=false` and is covered by `13/13` profile and `23/23` validator
tests. Its synthetic preflight is retained at
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\kaishek-court-position-synthetic-preflight-20260902.json`
(SHA-256
`B2183C32C18D0F7A6F00A8C96C2D0DEEAD7EAF8BFC358606F92415368E6674B7`), GREEN;
the rebuilt JAR SHA-256 is
`DCCCF51A8B68EEC6CCF8D391D7B0E839361DECB9E37098C31BBB78EB296247A1`.
No parent full preflight or CK3 run was repeated. This remains an offline
schema accelerator and does not change any live/readiness gate.

## 2026-09-02 10:45 `war_days` schema slice

The accelerator is clean at `main == origin/main ==
36b4743d5da013ba1f85790ebcffad2629442ed1`. It adds the exact-build-backed
`war_days` scalar descriptor as `TRIGGER/WAR/INTEGER`, with
`certified=false`; no native evaluator or runtime certification is claimed.
Focused profile, validator, and ZhongGuo fixture tests passed (`14`, `24`, and
`12`), the CLI smoke is GREEN, and GitHub CI run `33584241395` succeeded. The
rebuilt JAR is 317,764 bytes with SHA-256
`DFEA464B657D627BBB1AEF34C12CD91419830644D47F891782A3C9D718C44D61`.

The parent-adapter artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-fresh-semantic-ready-20260902T1042-war-days\open-kaishek-preflight-war-days.json`
(SHA-256
`CDC7DCD22888208C7585A2932F266912CAE4C08A9D0836D7EF6580796FC8571F`).
The product parser is GREEN (`76/23,831,335/0`), the bounded root validator is
the expected schema-only RED (`232,973` unsupported diagnostics), and the
dedicated `ck3-war-days-trigger-11906` fixture has parser/validator GREEN with
IR/runtime explicitly SKIPPED. The run is offline
(`ck3_started=false`, `save_mutated=false`, `network_used=false`) and does not
alter phase-two or G2 live readiness.

## 2026-09-02 11:00 `has_innovation` schema slice

The canonical accelerator advanced cleanly to `main == origin/main ==
dad0ea2a864cbb4b9ea4a4e9dd388f606485830a`. The exact-build-backed
`has_innovation` descriptor is a syntax/profile slice only:
`TRIGGER/CULTURE/STRING`, zero parameters, deterministic/read-only, and
`certified=false`. The profile/runtime `CULTURE` type bridge, fixture,
validator, and CLI smoke tests all pass; no native evaluator or runtime
certification is claimed. The exact-build static evidence records evaluator
RVA `0x282CE90` and the culture/innovation storage anchors in the open_k
contract. The rebuilt CLI JAR is 319,753 bytes with SHA-256
`478D2F4040316C5223470BB350AF286256D78ECA3EB7B413B0383EEF88B86911`, and
GitHub CI run `33585124901` succeeded.

The current-adapter fixture-only artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\kaishek-has-innovation-adapter-fixture-only-20260902.json`
(SHA-256
`A8F852B8586F0AEC3975B75E7A118105286C79E9E64D2C7E8D26EFAADAEA317B`). It
binds the exact open_k commit/JAR and stable adapter contract `b306a95`;
fixture parser/validator are GREEN and IR/runtime are explicitly SKIPPED.
The full-root companion preflight remains the known bounded validator RED
(`232,973` diagnostics). Both runs are offline (`ck3_started=false`,
`save_mutated=false`, `network_used=false`), so this increment does not
change phase-two or G2 live readiness.

## 2026-09-02 11:20 `has_cultural_tradition` schema slice

The accelerator advanced on its minimal fast-forward path to
`main == origin/main == fd85dd6` (implementation `f12a0a9` plus the
preflight registration commit `fd85dd6`). The exact-build-backed
`has_cultural_tradition` descriptor is `TRIGGER/CULTURE/STRING`,
deterministic/read-only, and `certified=false`; profile, validator, dedicated
fixture, CLI, full Maven, and package checks passed. Static evidence binds the
exact-build evaluator at RVA `0x282D990` (376-byte slice SHA-256
`2073F14B5611955D899F21A35DD945239EE325C2EAD6652EBA1DBCBE5CAC78A9`) and the
culture/tradition storage anchors. No runtime evaluator or CK3 live claim is
made. The rebuilt CLI JAR SHA-256 is
`D94929A6ADF8140483962137E01B6B1319E88216EDD2B6E68612DF286A1CFEF8`, and
GitHub CI run `33586554036` succeeded.

The current-adapter fixture-only preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\kaishek-has-cultural-tradition-20260902.json`
(SHA-256
`AB96FBF00CFC4D491FADEABE8F82CB485A8A48B1CDCF68315C87B0DEB80474FF`). It
binds the current open_k commit/JAR; fixture parser/validator are GREEN and
IR/runtime are explicitly SKIPPED, with
`ck3_started=false`, `save_mutated=false`, and `network_used=false`. This
offline slice leaves phase-two and G2 readiness unchanged.

## 2026-09-02 11:40 culture schema follow-up

The canonical accelerator then advanced on the same minimal fast-forward path
to `main == origin/main == e92b94f8b4cc03f1a91afafaf2a23f5e4560a1e4`.
Two exact-build-backed, syntax/profile-only culture triggers are now present:
`has_cultural_pillar` (`89141b3`) and `has_cultural_parameter` (`e92b94f`),
both `TRIGGER/CULTURE/STRING`, deterministic/read-only, and
`certified=false`. Neither adds a runtime evaluator or changes CK3 behavior.

The pillar slice binds evaluator RVA `0x282D900..0x282D97B` (124-byte SHA-256
`7B8B0972F9A0324E408E4B9DE88C209BF9CE52409091BA934303BF8596D28054`) and
uses the selected-culture pillar span/count and key anchors. Its rebuilt CLI
JAR is SHA-256
`DBE1ECA09FDE50DB43E0537BCFDBB7554E11F3D5229AD1319BBB6B71F286BDF6`; the
dedicated parent preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-fresh-semantic-ready-20260902T1140-cultural-pillar\open-kaishek-preflight-cultural-pillar.json`
(SHA-256
`33A62106B3F129A480129308359981F72A13DE32F4253A58062F91CEDE6E018E`).

The parameter slice is covered by the dedicated fixture artifact
`Z:\ck3_mod_rewrite_process_assets\zg361\kaishek-has-cultural-parameter-20260902.json`
(SHA-256
`D834CE5998C5DB697894A608F2A971051D5F45E8FEDFCD8C9F67682DB8B2FA78`) and
the rebuilt JAR SHA-256
`98029BA80F688A49BF18116EF9A3DDCF61AB9C61E51F9371CBF7736E3DB6C316`.
The focused profile/validator/ZG361 suites are GREEN (pillar `17/27/18`,
parameter `18/28/20`); both fixture preflights report parser/validator GREEN,
IR/runtime SKIPPED, `ck3_started=false`, `save_mutated=false`, and
`network_used=false`. The full-root `cli-red`/bounded validator result in the
pillar artifact is the known schema-only corpus boundary, not a slice failure.
These increments improve offline acceleration only and leave phase-two loader
and G2 `GEN-034` readiness unchanged.

## 2026-09-02 12:40 `is_acclaimed` schema slice

The canonical accelerator advanced to `main == origin/main ==
638f4c0`.  The new exact-build-backed `is_acclaimed` descriptor is a narrow
`TRIGGER/CHARACTER/BOOLEAN` shape with zero parameters, deterministic
read-only metadata, and `certified=false`.  It enables parser/validator
preflight for the Character leaf used by the combat manifest; it does not
introduce an `ACCOLADE` scope, a native evaluator, or runtime certification.

Focused profile, validator, ZG361 fixture, package, and CLI smoke checks were
GREEN.  The retained parent preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\kaishek-is-acclaimed-20260902.json`
(SHA-256
`D48913E0F4A831B0220EE2A818393CB3AA42B88D8B976097CF9652DEF30FFC73`).
Its dedicated fixture parser/validator stages are `1 file / 163 bytes /
0 diagnostics`; IR/runtime are explicitly `SKIPPED`, with
`ck3_started=false`, `save_mutated=false`, and `network_used=false`.  The
rebuilt CLI JAR SHA-256 is
`D1341CD872D07E8081A4E53040655C420FB4A8EEDD24DC5DE616761CDFF068A2`.
The two initial CI failures were caused by a missing preflight registration;
the follow-up commit `638f4c0` contains that fix, while its final CI was still
in progress at handoff.  No phase-two or G2 readiness label changes.

## 2026-09-02 12:45 `can_be_acclaimed` schema slice

The accelerator then advanced to `main == origin/main == 759199b`.  The
exact-build-backed `can_be_acclaimed` descriptor is a schema-only
`TRIGGER/CHARACTER/BOOLEAN` shape with zero parameters, deterministic
read-only metadata, and `certified=false`.  It is intentionally separate
from `is_acclaimed`: the native leaf at `0x2819200` enters the full
qualification evaluator `0x28A4870`, but this slice does not invoke that
evaluator, add an `ACCOLADE` scope, or claim runtime semantics.

Profile, validator, ZG361 fixture, OfflinePreflight, package, and CLI smoke
checks passed once.  The parent preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\kaishek-can-be-acclaimed-20260902.json`
(SHA-256
`503BA9C9F7D49E4154BC6B0FD29E763A59FD1AAC1BA3AED24767C29DC4ABE409`).
Its parser/validator stages are `1 file / 163 bytes / 0 diagnostics`,
IR/runtime are `SKIPPED`, and `ck3_started=false`, `save_mutated=false`,
`network_used=false`.  The rebuilt CLI JAR SHA-256 is
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
The final open_k CI runs `33592356916` and `33592340523` both completed
successfully; no parent CK3 or G2/phase2 readiness label changed.
