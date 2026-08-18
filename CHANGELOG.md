# Changelog

## [1.0.0] - 2026-08-18

### Added

- One-ruler CK3 Roguelite / New Game+ loop with exact death settlement and cross-save Ember Tiers.
- Absolute and lifetime-growth challenge tracks with uncapped 0%, 25%, 50%, or 100% inheritance; Growth + 100% is the recommended default.
- Six lifetime contract archetypes, behavior scoring, persistent per-contract PBs, grades, and collection progress.
- Ten Glassfire Gaze milestones alternating favor rerolls and curse seals.
- Stable pool wire IDs, visible rarity/build labels, applicability filters, and state/contract weighting.
- Glassfire Ledger, first-life guidance, deterministic release staging, static CI, and production smoke scenarios.
- High-tier shop sinks: Grand Tribute (10,000), Borrowed Generation (50,000), and Sixfold Apotheosis (100,000).

### Changed

- Favor sessions now contain one blessing/curse pair every three years instead of up to three pairs per session.
- Record writes compare quantized candidate tiers rather than exact scores.
- Shop prices use consistent integer rounding; inherited budgets preserve the selected ratio without a separate spending cap.
- Growth scoring and ledger gaps use CK3's `min = 0` lower-bound semantics instead of incorrectly clamping positive values with `max = 0`.
- Scoring implementation, preview, reference model, and documentation share one schema.
- Lifespan purchases now describe their actual +1 Health stacks instead of promising a fixed number of years.

### Requirements

- Crusader Kings III 1.19.0.6.
- Tutorials set to Full or Warnings so new Ember Tiers and contract PBs can persist.
- New single-player game recommended.

### Known Limitations

- Existing Ember Tier bits are shared progression; the selected challenge track is explicitly labeled rather than stored as eight separate historical score namespaces.
- The no-heir settlement fallback is statically covered but can still be obscured by the native Game Over presentation.
- Acceptance-only scripts remain packaged until the test overlay is fully separated, though normal play cannot trigger them.
- 1.0 contract narrative is authored in Simplified Chinese and English; seven other language files currently use English pending human translation.
