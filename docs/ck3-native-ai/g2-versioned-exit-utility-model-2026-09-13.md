# G2 versioned Raiktor exit utility model (2026-09-13)

Status: **strategy-model static-ready; same-frame evaluation and action remain false**.

## Problem closed by this package

The earlier owner-model provider accepted only an externally authored and
explicitly approved file. No such file existed, so the G2 critical path could
never progress from observed terms to a comparison. That approval requirement
was a workflow policy rather than a CK3 runtime constraint. It is retained for
legacy callers, but is no longer the only strategy-model source.

The new `raiktor_exit_utility_model_provider.py` selects a complete versioned
repository default when no path is supplied. An explicit operator override is
also supported, but must identify the repository default model it replaces.
Both paths bind the exact model bytes and the exact current repository budget
profile bytes by SHA-256.

## Active baseline

The source is
`ck3_autonomous_player/strategies/raiktor_exit_utility_v1.json`:

- source contract `raiktor-strategy-exit-utility-model-source-v2`;
- model `raiktor-exit-balanced-utility-v1 / 1.0.0`;
- source SHA-256
  `9AE47EB324850C8FF6BABE242DFEA6F09F76C175827E3BEAD2AC5875C52D84E0`;
- utility unit `strategy_utility_q100000`;
- exact binding to budget profile `raiktor-exit-balanced-v1 / 1.0.0`,
  source SHA-256
  `4206D725EC702701725221EB274E1F248E607F3127B720D033779FD71154FD11`.

The coefficient inventory covers the terms already named by the exit
contracts: primary gold transfer, attacker prestige delta, removed claims,
favor, truce duration, PoW release, title-holder changes, hostage transfers and
war-bound soldier loss. The model also names three supported policy rules:
hard-budget rejection, a capped penalty for explicitly unobserved effects, and
a continue-war tail penalty selected from measured power relation.

These numbers are a replaceable project strategy baseline. They do not claim
to represent CK3's native AI, an inferred human preference or an owner-signed
approval. Any future tuning changes the source version and hash; a focused
operator override must bind the default model ID/version and the same budget
bytes.

## Readiness boundary

The provider returns `model_production_eligible=true` because the configuration
is complete and executable. It deliberately keeps all downstream gates false:

- same-frame utility evaluation;
- white-peace comparison;
- three-way decision;
- automatic surrender and GEN-034 closure.

Those gates require a supported evaluator plus a real paused observation. The
failed broad loaded-effect preview remains disabled after its two live crashes.
The next implementation step is the narrow white-peace projection for the
specific `raiktor_claim_cb` path, using the already stable per-effect readers.

## Verification

Focused provider tests pass in normal and optimized Python, `7/7` in each
mode. The generated provider receipt is:

`Z:\ck3_mod_rewrite\_runtime\g2-gen034-exit-utility-model-20260913\repository-default-model.json`

It is 3,310 bytes with SHA-256
`4BBFDA9EE48821973F9E3D9A50117A18AA4B0CCE0AF9D2EB6DA5B6B30A03951C`.
No CK3 process, DLL, game file, save or desktop input was used.
