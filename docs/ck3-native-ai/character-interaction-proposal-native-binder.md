# Character interaction proposal native binder

Status: **static-ready, private and unwired** for CK3 `1.19.0.6`. No CK3 process was started for this work, and no public schema, MCP method, shared CMake target, or bridge registration was changed.

This binder connects the eleven semantic proposal actions in DIPLO4 to CK3's existing generic character-interaction command spine. The five actor/recipient-only interactions use the stock two-role context constructor. Education, ward, guardianship, grant titles, grant vassal, and ransom require the typed source added by DIPLO5 plus a definition-specific private materializer. A later glue owner must provide both the paused preview capture and those six materializers; this package does not guess special payload memory.

## Exact-build command path

The frozen executable is `ck3.exe` `1.19.0.6`, size `95,206,008`, SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`. The ABI manifest hashes 64-byte spans at every callable code entry.

The binder resolves the loaded interaction definition through database getter `0x831890`, stable-key hash `0x3B8B000`, and lookup `0x997930`. It resolves actor and recipient from `module+0x570C130` by low-24-bit slot and then requires the complete signed generation-bearing `CharacterID` at `Character+0x18`.

For the five ordinary rows, context construction uses `0x2C3EE50`. Every reconstructed `0x338` context then passes refresh `0x2C40950`, finalize `0x2C40B20`, an identity reread, and fresh complete Can Send `0x2C43F00`. A false Can Send is a RED rejection and no command is constructed.

The exact command constructor at `0x26B3220` produces a caller-owned `0x368` command. The binder requires primary vtable `module+0x40829F8` at `+0x00`, secondary vtable `module+0x40829C8` at `+0x18`, and an identity-equivalent copied context at `+0x20`. Submission uses the existing command manager at `module+0x57621F0`, `SubmitCommand` at `0x973E00`, and player flags `0x0E`.

## Typed payload preservation

DIPLO4 already compares two complete preview envelopes before its single submit callback. This binder additionally compares the two DIPLO5 typed sources. For each of the six special rows, the rebuilt context is read through DIPLO5 again after refresh/finalize; the command's embedded context is read the same way after the stock copy constructor. Full primary and secondary role IDs, intermediary, exact selected-option mask, ordered full title IDs, semantic payload, and fingerprint must all match the captured source.

This keeps the education faith option deferred by DIPLO5. It also prevents a grant-title list, ward/guardian pair, transferred vassal, or ransom option from changing between preview and queue insertion.

Both caller-owned contexts follow the existing CK3 lifecycle. The source context and command-embedded copy are each destroyed exactly once through `0x2C3F380` after the synchronous queue-clone call. A partially constructed object is destroyed only when its definition pointer proves that construction established ownership.

## Result boundary

The binder permits one queue attempt. `SubmitCommand=true` yields only DIPLO4's `submitted_verification_pending` ACK. It does not prove a gift, move to court, vassalization, education relation, title transfer, vassal transfer, or ransom outcome. DIPLO4's later, newer paused interaction-specific receipt remains the sole success authority.

Wrong build identity, address drift, capture drift, stale character generation, typed reconstruction mismatch, complete Can Send false, command vtable/context mismatch, and queue rejection remain explicit RED failures. They are not converted to warnings or success receipts.

## Offline verification

The native fixture covers exact environment/configuration gates, a successful ordinary submit with both owned contexts cleaned, typed education reconstruction and DIPLO5 reread, typed capture/materialization drift, full-ID generation rejection, fresh Can Send false, command vtable mismatch, and queue rejection. It is compiled independently because this package deliberately does not modify shared CMake.

```powershell
# Run from a VS x64 developer shell, with separate output directories.
cl /std:c++20 /Od /W4 /WX /permissive- /EHsc /I ck3_autonomous_player/native_bridge/include `
  ck3_autonomous_player/native_bridge/src/character_interaction_proposal_action_core_v1.cpp `
  ck3_autonomous_player/native_bridge/src/character_interaction_proposal_payload_source_extension_v1.cpp `
  ck3_autonomous_player/native_bridge/src/character_interaction_proposal_native_binder_v1.cpp `
  ck3_autonomous_player/native_bridge/src/character_interaction_proposal_native_binder_v1_test.cpp

cl /std:c++20 /O2 /DNDEBUG /W4 /WX /permissive- /EHsc /I ck3_autonomous_player/native_bridge/include `
  ck3_autonomous_player/native_bridge/src/character_interaction_proposal_action_core_v1.cpp `
  ck3_autonomous_player/native_bridge/src/character_interaction_proposal_payload_source_extension_v1.cpp `
  ck3_autonomous_player/native_bridge/src/character_interaction_proposal_native_binder_v1.cpp `
  ck3_autonomous_player/native_bridge/src/character_interaction_proposal_native_binder_v1_test.cpp

py -B ck3_autonomous_player/native_bridge/research/verify_character_interaction_proposal_native_binder_v1.py --exe "<CK3>/binaries/ck3.exe"
py -B -O ck3_autonomous_player/native_bridge/research/verify_character_interaction_proposal_native_binder_v1.py --exe "<CK3>/binaries/ck3.exe"
```

## Live pending

The binder is not production-live. The next integration package must wire an application-main paused capture and all six special materializers, keep the candidate build fixed, and obtain a real CK3 proposal submit followed by the mapped later world-state receipt. Public schema and MCP claims remain out of scope until that live evidence is GREEN.
