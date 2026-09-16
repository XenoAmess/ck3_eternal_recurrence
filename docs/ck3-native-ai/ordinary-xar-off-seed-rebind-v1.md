# Ordinary `xar_off` seed rebind v1

## Purpose and boundary

An ordinary-campaign seed copied to another prepared state directory keeps the
same CK3 save bytes, but the target `xar-autoplayer-environment.json` has a new
digest because its state/profile/runtime paths are different.  Driver-state v2
correctly rejects that copied seed until its lifecycle binding names the target
prepared environment.

`xar_autoplayer.ordinary_seed_rebinder` performs that narrow migration without
launching CK3 or touching the opaque save.  It supports only
`ordinary_campaign_succession` + `xar_off` + the fresh-campaign no-pact
contract.  Rogue, legacy, unknown, mixed and missing bindings fail closed.

## Contract

Before writing, the rebinder verifies:

1. no managed `ck3.exe` process is alive;
2. the target profile passes `verify_profile(..., xar_enabled="xar_off")`;
3. driver-state is consumer-compatible v2 for its persisted pipe;
4. top-level `succession_lifecycle`, `last_checkpoint.succession_lifecycle`,
   and the matching successful `save-checkpoint` history result are present,
   identical and ordinary `xar_off`/no-pact;
5. `xar_checkpoint.ck3` size and SHA-256 match the driver checkpoint.

It replaces only those three lifecycle-binding objects with the binding derived
from the target prepared manifest.  It then reruns
`load_native_driver_state_for_resume` and
`validate_cold_start_checkpoint_for_pipe`.  Any post-write RED restores the
original driver bytes atomically.  The save size, SHA-256 and bytes must remain
identical.

The v1 receipt records source/target environment digests, source/target driver
SHA-256, the unchanged save mapping, both post-rebind validator results, and
the exact expectations needed by the subsequent no-launch preflight.  The
receipt does not claim a cold restore or gameplay result.

## Operator integration point

After preparing the destination with `xar_enabled=xar_off`, copy the paired
`xar_checkpoint.ck3` and `driver-state.json` into their canonical target
locations, then run from the agent environment:

```powershell
python -m xar_autoplayer.ordinary_seed_rebinder `
  --state-dir <prepared-state> `
  --game-dir <frozen-ck3-directory> `
  --expected-pipe <persisted-pipe> `
  --receipt <artifact-directory>\ordinary-seed-rebind-v1.json
```

The preview operator should pass the receipt's
`no_launch_preflight_expectations` into the ordinary-aware no-launch preflight
before it exposes a start/resume command.  The operator must not select a new
pipe during this migration because pipe identity remains part of the cold
checkpoint anchor.
