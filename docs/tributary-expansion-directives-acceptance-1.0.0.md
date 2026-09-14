# Tributary Expansion Directives 1.0.0 acceptance

Status: **released and fresh-Workshop-cache GREEN**. The exact source release
projection and the independently downloaded Workshop copy both passed the same
bounded CK3 logic cell. Public metadata, full Change Notes, and gameplay media
were also read back anonymously.

## Exact live run

- Run: `tea_source_R0009`
- Artifact: `D:\workspace\ck3_eternal_recurrence_process_assets\tributary_expansion_directives\runs\tea_source_R0009`
- Top report: `report.json`, result `GREEN`, SHA-256
  `B90D4C7EA94E3828EFB6A44F19398A1E35273DCB78CF0D996884AEC493A4D020`
- Started: 2026-09-14 16:00:54 Asia/Shanghai; duration 500.765 seconds
- CK3: `1.19.0.6`; executable SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- Product projection: exactly 16 release files; tree SHA-256
  `AAB1CF1AAA89955A6F4D3CA797688D8B7D2FD9EFF9F807D90BB3A1DE5473F6F3`
- Runtime product and fixture trees were byte-identical before/after. The
  canonical source and protected user storage were unchanged, project
  diagnostics were empty, the one-time userdir was removed, and CK3 exited.

## Fresh Workshop-cache replay

- Workshop item: [`3801490405`](https://steamcommunity.com/sharedfiles/filedetails/?id=3801490405).
- The target cache path did not exist before the explicit Steam Console
  `workshop_download_item 1158310 3801490405` command. Steam downloaded content
  manifest `8882580747800332818`: 16 files and 770,946 bytes.
- The ID-bearing sidecar manifest SHA-256 is
  `F6BAA803EA940DB99B111D2F2EDA825E39CA89697C75CB4175601472B372E078`.
  Exact inventory/size/SHA-256 verification passed 16/16 files, allowing only
  the canonical terminal `remote_file_id="3801490405"` descriptor line.
- Run: `tea_workshop_3801490405_R0010`; artifact:
  `D:\workspace\ck3_eternal_recurrence_process_assets\tributary_expansion_directives\runs\tea_workshop_3801490405_R0010`.
- Top report: `report.json`, result `GREEN`, SHA-256
  `6A42BAA0146C4B9AD286FA26B242836703046FCF266D467869ACB089589966E3`;
  duration 578.772 seconds.
- The fresh-cache run repeated the same direct-tributary, refusal, subsidized
  acceptance, and attacker/defender binding assertions. Product tree SHA-256
  remained `AAB1CF1AAA89955A6F4D3CA797688D8B7D2FD9EFF9F807D90BB3A1DE5473F6F3`,
  product diagnostics were empty, source/runtime/protected storage were
  unchanged, the isolated userdir was removed, and CK3 exited.
- The public readback matched the 38-character title, all 1,197 normalized
  description characters, and the 840-character/11-line Change Notes entry
  `1789376413`. The public page exposed exactly one real gameplay screenshot;
  its anonymous Steam CDN body matched the tracked JPEG byte for byte. See
  [`../workshop/tributary_expansion_directives_screenshots.md`](../workshop/tributary_expansion_directives_screenshots.md).

## Live-covered behavior

- Constructed and read back a real direct tributary relationship.
- Selected a neighboring county for which the production CB's exact
  `can_declare_war` check returned true.
- Valid refusal preserved the send cost: suzerain Prestige `-150`, both Gold
  balances unchanged, and no directed war created.
- Valid subsidized acceptance preserved the send cost, transferred exactly
  `ted_war_subsidy_value` from suzerain to tributary, and started one dedicated
  war.
- Read back the dedicated CB with the tributary as primary attacker and the
  selected neighboring independent ruler as primary defender.
- Every required terminal marker occurred exactly once. The fixture used a
  one-shot latch after player switching so a repeated GUI `on_start` callback
  cannot manufacture duplicate PASS evidence.

## Honest live gaps

Neither live run claims:

- production interaction-selector UI coverage;
- a live same-frame invalidation/cooldown-refund scenario;
- live victory, white-peace, or defeat resolution;
- save/reload or a measured post-war tribute delta.

The dedicated CB's county transfer, non-victory outcomes, truce and inheritance
definitions are covered by the L0 source contract and exact live parser load,
not by executed outcome markers. See
[`tributary-expansion-directives-test-plan.md`](tributary-expansion-directives-test-plan.md).

## Preserved RED lineage

R0001 through R0008 remain preserved under the same process-assets root. They
separately record the original startup-window miss, two product parser
diagnostics, the invalid-target atomic refund path, an arbitrary non-declarable
fixture target, the wrong suzerain war-list lookup, a brittle pause closeout,
and a duplicated GUI callback marker. No RED attempt was overwritten or
relabeled GREEN.
