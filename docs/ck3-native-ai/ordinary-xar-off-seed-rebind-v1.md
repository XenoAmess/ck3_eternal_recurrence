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

Exact build `1.19.0.6-steam23530548` also writes an uncompressed binary SAV
variant.  Its observed header is `SAV` plus hexadecimal metadata, a newline,
then the binary marker `U1 01 00 03 00`; it does not start with the textual
`meta_data={` block.  The artifact inspector recognizes both native variants
as `raw-ck3` and reports `raw_header_kind` as `text` or `binary`.  Both remain
header-only format checks and still require the checkpoint's full byte count
and SHA-256 binding.

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

## Formal CLI and operator integration

The rebinder remains directly runnable as a module for focused development,
but the supported agent CLI is:

```text
python ck3_autonomous_player\agent.py --state-dir <prepared-state> --game-dir <frozen-ck3-directory> rebind-ordinary-seed-v1 --expected-pipe <persisted-pipe> --receipt <artifact-directory>\ordinary-seed-rebind-v1.json
```

Users prepare portable ordinary preview state through
`tools/g2_preview_operator.py prepare-state`.  After preparing the destination
as `xar_off` and copying the paired artifacts, the operator calls this formal
agent subcommand with the manifest's exact pipe.  It persists the receipt at
`<state-dir>/ordinary-seed-rebind-v1.json`, validates its schema and lifecycle,
then passes `no_launch_preflight_expectations` into the ordinary-aware
no-launch preflight.  After that gate passes, it verifies the rebound driver
bytes and atomically records the environment and driver hashes in the operator
manifest.  The operator never selects a new pipe because pipe
identity remains part of the cold checkpoint anchor.  A failed rebind or
preflight exits nonzero without launching CK3.
