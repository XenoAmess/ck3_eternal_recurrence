# Native71: copied physical state at the installed transfer boundary

The existing actual4 `291CF30` installed transfer hook now retains copied A/B state immediately before its one original call and after that same call returns. It uses the existing exact caller `2A3DC49`, preparation association, original return preservation, shared process clock, and retained record. The new data is an optional owned `PersonTransferPhysicalPostimage12004` on `PersonInstalledTransferCaptureRecord12004::physical_postimage`.

The source contract was frozen in external `continuation-13c/SOURCE-CONTRACT-FROZEN.json` before this change. It references the retained actual caller/state-exchange source in continuation-13, its closed caller suffix, the current adopted five-file baseline, and continuation-29b's frozen four-block inputs. No new game source sampling, PC kernel census, native getter, allocator invocation, or state-exchange replay was used to implement these observations.

## One original occurrence

`PersonInstalledTransferBindings12004` has borrowed `physical_observer_context`, `before_original_observer`, and `after_original_observer` callbacks. The before callback runs after the retained preparation and owner association have been copied, immediately before the sole original. The after callback runs after the original returns and the completed event and identity facts are formed. Unmatched original callers keep the existing bypass behavior.

The installed capture constructs a local probe for each invocation. Its callbacks call `CapturePersonTransferPhysicalPair12004` using the already bound guarded reader. They borrow the stage's existing before/completed clock events. `JoinPersonTransferPhysicalPostimage12004` forms the retained comparison after the stage completes. Neither the aggregate nor its adapters create clocks, counters, getter calls, hooks, or another original call. Separate invocations do not share a probe.

Each phase copies both actual Model A and Model B. The four independent blocks are:

| Model offset | Copied operand | Producer |
| --- | --- | --- |
| `+10` | Ordered opaque 16-byte rows and its own raw header | continuation-29 row copier |
| `+78` | Ordered raw U16 keys and its own raw header | continuation-30b adapter |
| `+E0` | Ordered Q64 value bits, signed source interpretation, and its own raw header | continuation-31b adapter |
| `+248` | Ordered raw 64-bit payload and its own raw header | continuation-32b adapter |

Default limits permit at most 64 KiB of payload per block, per side, per phase: 16 separately bounded operands, totaling at most 1 MiB of source payload. Descriptor, vector, signed/raw representation, retained record, and JSON overhead are additional. A block exception or unavailable operand remains partial without discarding another block's successful copy. Each block uses its own signed count; the aggregate does not substitute one block's count for another.

The shared clock and original occurrence establish observation ordering. Ordered copied payload equality establishes an observed before/post relation. Neither equality nor an empty payload proves that every native delegate executed a particular causal operation. Pointer/capacity cross equality is reported separately because elementwise exchange can preserve storage pointers and capacities.

## Retained wire and consumption

The existing standalone capture serializer adds `records[i].physical_postimage`. It is `null` when absent and otherwise uses schema `xar.ck3.person-transfer-physical-postimage-12004-v1` with full `before`, `after`, and `comparison` objects. Each phase preserves A/B scope, raw headers, declared counts, independent descriptor/payload completeness, ordered payloads, reasons, and budgets. Optional comparisons serialize as `null`, `false`, or `true` without collapsing unknown into empty or false.

Opaque rows serialize as ordered 32-character hexadecimal byte strings. U16 keys remain JSON integers. Value and tail raw 64-bit payloads serialize as exact `0x` plus 16-digit hexadecimal strings. The optional signed Q64 values are additional source interpretation; consumers can preserve raw bits without floating point or JavaScript integer conversion.

Continuation-57c retains the same owned transfer record before its actual Ci getter. Its `installed_transfer_lineage.physical_postimage_owned_at_consumption` marker reports that record's optional presence, including false when absent. The already owned `capture_at_consumption.records[0].physical_postimage` contains the complete payload. A later history query does not replace it. The validated character query continues to filter records by already resolved pointer and full generation-bearing ID.

Numeric history consumers must independently compare the retained completed preparation PC with before-B's ordered keys, Q64 bits, and counts; establish the copied before-B to after-A payload direction; and compare after-A with the same Ci's actual copied PC. `B+10` and `A+10` remain distinct identities. An owner/descriptor association or optional-presence marker supplies none of those numeric comparisons.

The serializer keeps `all_native_delegate_postimages_ready`, `retained_preparation_numeric_payload_compared`, `actual_Ci_numeric_payload_compared`, `full_person_ready`, and `entry_ready` false. The original identity stage's conservative readiness flags are unchanged.

## Validation and adoption

The new compound exports and calls continuation-29b's ten new cross-block scenarios, then exercises the actual installed synthetic CALL boundary, retained four-block postimage, real Native65 preparation support, one actual Ci getter, and its full retained consumption wire. The initial compiler attempt produced all 15 production/fragment objects and failed only on four unqualified members in the new fixture's static reader. The necessary correction is preserved separately from the initial failed source; the retry recipe recompiles only that fixture and reuses those objects and retained dependencies.

The necessary fixture-only retry compiled with MSVC `/W4 /WX` and the one new compound process returned zero. All ten aggregate scenarios and the installed boundary, completed Native65 preparation, one Ci getter, copied partials, and immutable retained wire checks passed. The 15 production/fragment objects were reused unchanged. The actual stdout produced four JSON artifacts: the full transfer, full consumption query, independent descriptor partial, and independent payload partial. The exact effective pins and receipts are external `continuation-13c/DELIVERY.json` and `fixture-retry01/ACTUAL-WIRE-EXTRACTION.json`.

Defender registration has a separate `settings_failed` receipt: `admin_required_for_verified_readback; no Add attempted and no UAC bypass`. Actual administrator registration remains pending. Prior continuation-13/13b qualifications and frozen input bytes remain historical qualifications; they were not replayed to credit this path. This compound uses owned synthetic memory and executable pages, and supplies no CK3 live acceptance.

Root owns adoption, Git, formal build, and lifecycle decisions. The current running R0088 is not replaced. Continuation-60 owns CMake registration: the aggregate, three thin adapters, and new physical serializer are registered once as unconditional provider TUs. The existing production runtime supplies the changed stage/capture/consumption implementations. The new compound target adds only the new main and the exported aggregate scenarios to that runtime; it does not duplicate production TUs in one binary.

Cold startup and explicit quiescence requirements from the installed hook remain in force. Stop or DllMain alone does not establish live quiescence, so this incremental patch introduces no new teardown path. External evidence follows storage policy 1.0.0 with finite review/protection deadlines recorded in the task close receipt.
