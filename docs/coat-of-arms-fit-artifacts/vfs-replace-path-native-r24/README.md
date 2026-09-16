# CK3 CoA `replace_path` native R24 (hypothesis RED)

This artifact preserves a falsified pre-registered hypothesis. It must not be
rewritten as GREEN.

## Scope

- CK3 exact build: `1.19.0.6`
- repository source: `ca510db1c572394859600ab50d292cfe62cb1f21`
- interaction: managed typed MCP only; no OCR, keyboard, mouse, or fixed screen
  coordinates
- fixture load order: an earlier directory mod, then a later directory mod
  declaring `replace_path="gfx/coat_of_arms/patterns"`
- capture: calibrated reference-free 230×230 native framebuffer crops
- capture-noise gate fixed before the run: maximum channel error `1`, normalized
  MAE `<= 0.00001`, alpha differing pixels `0`

## Pre-registered hypothesis and result

The R24 hypothesis said the earlier-mod-only pattern would behave like a
never-present missing pattern after the later mod's `replace_path`. That pair
failed decisively: all `46,518` common visible pixels differed, normalized MAE
was `0.3960397086`, and maximum channel error was `201`.

The other two pre-registered non-equivalence checks passed:

| Pair | Expected | MAE | Max channel error | Gate |
| --- | --- | ---: | ---: | --- |
| earlier-mod-only / missing control | equivalent | `0.3960397086` | `201` | **RED** |
| earlier-mod-only / later reference | different | `0.2679906042` | `178` | GREEN |
| missing control / later reference | different | `0.3844581632` | `201` | GREEN |

All 3/3 Apply, native Copy, route-stable preparation and reference-free
captures succeeded. Cleanup proved the CK3 process tree gone and released the
shared slot. Therefore this is a semantic-hypothesis RED, not a transport,
route, capture, or cleanup failure.

## Interpretation boundary

R24 proves that this later `replace_path` did **not** make the earlier enabled
mod's registered pattern behave like a missing resource. It does not yet prove
whether the same `replace_path` hides a base-game-only pattern. R25 adds that
independent base-game control while preserving this R24 result unchanged.

The complete raw report remains at
`D:\ck3_coa_vfs_replace_path_r24\report.json` on the evidence machine. Its
SHA-256 is
`1B095A14E9E31791F0F23E47DD82D952E00614D175223492E09F3FF56464772C`.
The fixture receipt SHA-256 is
`8A27DD6227180FEFCB75EA3599FB2C09113FE4108DF6E21ADCFBB2DC1BBF5F55`.
The three crop hashes and exact metrics are frozen in [summary.json](summary.json).

