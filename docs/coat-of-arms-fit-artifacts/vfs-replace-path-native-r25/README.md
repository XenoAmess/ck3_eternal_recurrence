# CK3 CoA `replace_path` native R25 (second hypothesis RED)

This artifact preserves a second falsified pre-registered hypothesis. It must
not be rewritten as GREEN or merged into the R24 artifact.

## Scope

- CK3 exact build: `1.19.0.6`
- repository source: `8a4114595172564227309f21250316e82fe68644`
- interaction: managed typed MCP only; no OCR, keyboard, mouse, or fixed screen
  coordinates
- fixture load order: an earlier directory mod, then a later directory mod
  declaring `replace_path="gfx/coat_of_arms/patterns"`
- controls: a base-game-only pattern, an earlier-mod-only pattern, a
  never-present missing pattern and a later-mod reference pattern
- capture: calibrated reference-free 230×230 native framebuffer crops
- capture-noise gate fixed before the run: maximum channel error `1`, normalized
  MAE `<= 0.00001`, alpha differing pixels `0`

The isolated profile's `dlc_load.json` enabled both fixture mods in the intended
order. The later descriptor hash-bound the exact `replace_path`; CK3's debug log
reported both mods enabled and both data roots mounted.

## Pre-registered hypotheses and result

R25 split the R24 successor into two assertions:

1. base-game-only `pattern_checkers_06.dds` should behave like a never-present
   missing control after the later `replace_path`;
2. the earlier enabled-mod pattern should remain available and differ from the
   missing control and later reference.

The second assertion passed, but the first failed decisively. Every one of the
`47,786` common visible pixels differed between the base-only and missing
captures; normalized MAE was `0.3996776478` and maximum channel error was `201`.

| Pair | Expected | MAE | Max channel error | Gate |
| --- | --- | ---: | ---: | --- |
| base-only / missing control | equivalent | `0.3996776478` | `201` | **RED** |
| base-only / later reference | different | `0.2704351016` | `178` | GREEN |
| earlier-mod-only / missing control | different | `0.3996766357` | `201` | GREEN |
| earlier-mod-only / later reference | different | `0.2704324482` | `178` | GREEN |
| missing control / later reference | different | `0.3767219267` | `201` | GREEN |

All 4/4 Apply, native Copy, route-stable preparation and reference-free
captures succeeded. Cleanup proved the CK3 process tree gone, watchdog absent,
control files removed and shared slot released. This is therefore a
semantic-hypothesis RED, not a load configuration, transport, route, capture or
cleanup failure.

## Interpretation boundary

For this exact 1.19.0.6 CoA pattern fixture, the loaded descriptor's
`replace_path` did not make either the base-game-only pattern or the earlier
enabled-mod-only pattern behave like a missing resource. The evidence does not
prove that CK3 ignores `replace_path` globally, nor does it reveal the runtime
VFS/CoA registry source that supplied each resource.

The next investigation therefore needs structured runtime provenance rather
than another post-hoc framebuffer expectation. Until that MCP capability or an
equivalent exact-build observation exists, the production asset-pack contract
must not infer `replace_path` winner semantics.

The complete raw report remains at
`D:\ck3_coa_vfs_replace_path_r25\report.json` on the evidence machine. Its
SHA-256 is
`6D130D2A979DA43948EA161FCB2A7CC058AEAC3D6806ACC672BF3D94757508DD`.
The fixture receipt SHA-256 is
`CB98296481697372B6A7AF1E7CCDED6613ED92D53BCEA3020C6882783E3E9096`.
Exact crop hashes and metrics are frozen in [summary.json](summary.json).

