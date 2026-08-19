# Changelog

## [1.0.0] - Unreleased

### Added

- One-ruler CK3 Roguelite / New Game+ loop with exact death settlement and cross-save Ember Tiers.
- Absolute and lifetime-growth challenge tracks with uncapped 0%, 25%, 50%, or 100% inheritance; Growth + 100% is the recommended default.
- Six lifetime contract archetypes, behavior scoring, persistent per-contract PBs, grades, and collection progress.
- Ten Glassfire Gaze milestones with native attribute growth and increasingly rich reroll/seal rewards.
- Stable pool wire IDs, visible rarity/build labels, applicability filters, and state/contract weighting.
- Glassfire Ledger, first-life guidance, deterministic release staging, static CI, and production smoke scenarios.
- High-tier shop sinks: Grand Tribute (10,000), Borrowed Generation (50,000), and Sixfold Apotheosis (100,000).
- A fourth shop page with purchasable rerolls, seals, Dread, Legitimacy, and Tyranny relief.
- A native succession-window settlement for runs ending without a playable heir.
- A paid custom-courtier commission with persistent per-player choices for sex, age, education, commander, congenital, and personality traits. This candidate source is not release-approved until its pending L0 and CK3 checks pass.

### Changed

- Favor sessions now contain one blessing/curse pair every three years instead of up to three pairs per session.
- Record writes compare quantized candidate tiers rather than exact scores.
- Shop prices use consistent integer rounding; inherited budgets preserve the selected ratio without a separate spending cap.
- Growth scoring and ledger gaps use CK3's `min = 0` lower-bound semantics instead of incorrectly clamping positive values with `max = 0`.
- Scoring implementation, preview, reference model, and documentation share one schema.
- Lifespan purchases now describe their actual +1 Health stacks instead of promising a fixed number of years.
- French, German, Japanese, Korean, Polish, Russian, and Spanish now have translated source text instead of English structural placeholders. Human terminology/persona review and in-game truncation checks remain pending.
- Release staging excludes acceptance-only files and strips marked development instrumentation from mixed production files.

### Requirements

- Crusader Kings III 1.19.0.6.
- Tutorials set to Full or Warnings so new Ember Tiers and contract PBs can persist.
- New single-player game recommended.

### Known Limitations

- Existing Ember Tier bits are shared progression; the selected challenge track is explicitly labeled rather than stored as eight separate historical score namespaces.
- The no-heir result requires a generated projection of CK3's native succession window; another mod overriding the same GUI file can conflict, and a CK3 update requires regenerating and reviewing the projection.
- The current candidate has not completed validation after the custom-courtier commit. The dedicated with-heir death scenario and full `count|king|emperor|synthetic` 30–40 year matrix also have no current GREEN report.
- All nine languages have source text, but none has completed the release-level human terminology/persona and in-game truncation sign-off.
