# Phase 2 safe-core next-domain closure (2026-09-03)

This note records a read-only, whole-file static scan starting from the exact
55-file `p2-safe-core-abi` disposable product.  It does not change the
canonical mod tree and it did not start CK3.  “Closed” below means that the
selected files' custom scripted effect/trigger/value names, delayed event IDs,
and localization keys resolve for the selected language.  It is a static
closure claim, not a live or feature-complete claim.

## Baseline

The baseline is
`_runtime/phase2-next-increment-safe-core-20260903/product` (55 files,
7,325,646 bytes).  It already contains the case-kernel pair, the current
`common/scripted_triggers/zg361_triggers.txt`, the current
`common/script_values/zg361_values.txt`, and the incident/manager runtime value
files.  The baseline projection manifest SHA-256 is
`fff67d71b374dfe2de2d64d8512213251761e485e0d3e901a1d4df339edf9d75`.

The profile-control settings use `l_simp_chinese`; both English and Simplified
Chinese variants are listed because localization closure is language-specific.
Only one language fan-out is needed for a controlled development run.  A
language-neutral projection would add all nine language files and is therefore
not a 1–5-file increment.

## Smallest real (non-stub) domain increments

The following candidates are complete at the callable/value/event/localization
boundary for one active language.  They contain generated production runtime
code, not diagnostic no-op stubs.

| domain / language | exact added files (bytes; SHA-256) | files / bytes added | closure result |
| --- | --- | ---: | --- |
| B1 / English | `common/scripted_effects/zg361_b1_runtime_effects.txt` (495,777; `cdb388005ffeac6d332380e910fbbf929f49871047e118d047c63b8751c001b4`); `events/zg361_b1_runtime_events.txt` (29,639; `6576ea63f654d2321620a026471390f147b90719d98f69feea34f4c5779e8543`); `localization/english/zg361_b1_l_english.yml` (7,416; `785263213915bf78db886626f8459c3cc072a083cc93a5510b70d36c1ef829a7`) | 3 / 532,832 | callable=0, event=0, loc=0 |
| B1 / 简体中文 | same effect/event files; `localization/simp_chinese/zg361_b1_l_simp_chinese.yml` (7,136; `00320692c35e9ed6ddb0d02f9d1d988876f22aa72b966a3247efd87f9adac938`) | 3 / 532,552 | callable=0, event=0, loc=0 |
| Incident / English | `common/scripted_effects/zg361_incident_platform_runtime_effects.txt` (700,085; `0c228faabb5f6d7dcdabfd32a071ca82f0c1ef15c08ab0bd07c25af3a467dacd`); `events/zg361_incident_platform_runtime_events.txt` (8,573; `49577d5475fbf6b22006021f4faded2a248c7e193840a283fb043f7aaac0e091`); `localization/english/zg361_incident_platform_l_english.yml` (7,807; `d34440516cba2b4a47f17c2156322eb8ff4f2a67193de42c0c00f58ab7827d52`) | 3 / 716,465 | callable=0, event=0, loc=0 |
| Incident / 简体中文 | same effect/event files; `localization/simp_chinese/zg361_incident_platform_l_simp_chinese.yml` (6,880; `9bfc502e21f3f4537cc7d4850898eafd46ad6daf2619a55ac9fe5e8375ab2b2a`) | 3 / 715,538 | callable=0, event=0, loc=0 |
| Manager / English | `common/scripted_effects/zg361_manager_governance_runtime_effects.txt` (386,750; `53120757ab63b1694a3c2b93ef4ac7a409a71300767ce93382720a246d0dab18`); `common/scripted_triggers/zg361_manager_governance_runtime_triggers.txt` (55,260; `eb2a522d12e72fc83a4a1566ee35a74153cf6a8238e001ba7a94aab78d56520c`); `events/zg361_manager_governance_runtime_events.txt` (8,303; `70cd4ed25f4bf9e480b6f2eb187cd498d315d5c1013d6401ee51786ceb0e7edf`); `localization/english/zg361_manager_governance_l_english.yml` (1,564; `71b36baf84f33ba4bf5e31d097ed6487fda1efa772ee079a46e6d8d6845683db`) | 4 / 451,877 | callable=0, event=0, loc=0 |
| Manager / 简体中文 | same effect/trigger/event files; `localization/simp_chinese/zg361_manager_governance_l_simp_chinese.yml` (1,647; `0d04a40f48aeaddbb5c9c9bc89e7870a95c5bd91e76e833a52fdb37b46cb2950`) | 4 / 451,960 | callable=0, event=0, loc=0 |

The resulting disposable projections have been materialized and replayed with
the projection utility (all replay checks GREEN):

- B1 English: `_runtime/phase2-next-increment-b1-closed-20260903-r1`, 58
  files / 7,858,478 bytes; manifest SHA
  `1a1976cfe745a38c8bf7e9c65e328b6c2f3b9a5640c5e5ed5cc80764e477a18b`.
- B1 简体中文: `_runtime/phase2-next-increment-b1-closed-zh-20260903-r1`, 58
  files / 7,858,198 bytes; manifest SHA
  `20346ba3eda3218bbebce3252ed955c0ca4ed4ad28e8d182681e2c12608e6359`.
- Incident English: `_runtime/phase2-next-increment-incident-closed-20260903-r1`,
  58 files / 8,042,111 bytes; manifest SHA
  `caddc1f8ade5ecd7b09986ca1f28ef808dd11a0d6af919d3afc9c11da4e4242f`.
- Incident 简体中文: `_runtime/phase2-next-increment-incident-closed-zh-20260903-r1`,
  58 files / 8,041,184 bytes; manifest SHA
  `602b94d963899d2fa7004e3a19bea75d21640bd0db8f33448b02a88c66b8c31c`.
- Manager English: `_runtime/phase2-next-increment-manager-closed-20260903-r1`,
  59 files / 7,777,523 bytes; manifest SHA
  `07b4dd38ec31f5ccbd400663047f9a0774620651600827208ea32430e76aa32d`.
- Manager 简体中文: `_runtime/phase2-next-increment-manager-closed-zh-20260903-r1`,
  59 files / 7,777,606 bytes; manifest SHA
  `d2b3d2e23a2e71e312b6290f6fa2f19db0402d4724834df3191bc3dc9d89b1e6`.

The source files remain in the full frozen source tree
`_runtime/phase2-full-exact-clean-20260903/mod_zhongguo_style`; no source file
was rewritten while making these projections.

## Why B2 has no 1–5-file production increment

The B2 runtime pair plus one language localization file is not closed:

- `common/scripted_effects/zg361_b2_runtime_effects.txt` (253,920 B) and
  `events/zg361_b2_runtime_events.txt` (33,691 B) are real generated code, and
  the active-language loc file is 3,298 B (English) or 3,172 B (简体中文).
- The effect/event pair has three distinct external production callables, each
  owned by a different file:

  1. `zg361_we_submit_al_357_359_receipts_effect` →
     `common/scripted_effects/zg361_workforce_endgame_runtime_effects.txt`
     (4,636,271 B; SHA
     `926453fe4b3621b5381743d61f5d03ac29c1d498181702e05a9532739d334d8a`).
  2. `zg361_workforce_probation_fact_publish_from_pip_settlement_effect` →
     `common/scripted_effects/zg361_workforce_probation_fact_effects.txt`
     (205,410 B; SHA
     `b0ea0b735c2ab7ae16ec22fd25ecdf8f37b0c0e7c2a44150ec2c0eb25e6a450e`).
  3. `zg361_workforce_normal_exit_fact_begin_from_m075_offer_effect` →
     `common/scripted_effects/zg361_workforce_normal_exit_fact_effects.txt`
     (61,629 B; SHA
     `7fde79fab6c1789fe0d4836a56d90ebc1384461679721632c520d66fa45fa4ef`).

Therefore any whole-file B2 projection that contains the effect, event, and
localization contracts needs at least `3 + 3 = 6` files, even before following
the owners' own dependencies.  Omitting the event file leaves 20 delayed B2
event IDs unresolved; omitting the B2 localization file leaves 35 active
language keys unresolved.  Replacing the three owners with no-op definitions
would be a diagnostic stub and is explicitly excluded from this candidate set.

For scale, a conservative whole-file fixed-point scan (English loc) added the
three direct owners, then 28 further workforce/manager effect, trigger, event,
and loc owners.  The resulting B2 closure was 34 added files over the
55-file baseline (89 total; 6,282,883 B of added payload) before any nine-
language fan-out.  After that fixed point, targeted callable/event/loc missing
sets were all zero.  This is evidence that B2 is materially larger than the
1–5-file target, not a reason to mount the broad workforce tree blindly.

## Use and limits

The three small candidates are static-ready, language-specific source
increments.  The shared acceptance seed still calls B1, Incident, Workforce,
and B2 roots together; using that seed unchanged with one candidate will
intentionally report the other roots as projection-missing.  A live test must
use a caller/fixture scoped to the selected domain, or be labeled
`PARSER/PROJECTION_RED`.  None of these artifacts is evidence of CK3 live
feature behavior until the root agent performs its exclusive launch and the
appropriate in-game action/observation gate.
