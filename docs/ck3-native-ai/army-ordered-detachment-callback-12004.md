# Ordered detachment callback source — actual CK3 1.20.0.4

Root's exact pin is CK3 **1.20.0.4**, Steam **25734779**, EXE SHA-256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
This October7/W41 work uses source `23c3c4bc7fdf261f46174d35db12732808523463`.
The callback is needed between the known detachment prefix and the ordered
next ArRg visit; it is never installed or invoked as a readonly getter.

Root approved a finite maximum377B/four reads. Actual fresh cost is exactly
**377B/four reads**: actual4 constructor209B, wrapper52B, one primary-slot
QWORD8B and directly reached core108B. Old constructor/wrapper caches were
reused. New metadata, old EXE bytes, hashes, whole scans, builds, tests,
native invocations and game operations are zero.

| Exact source | Proven direct role |
| --- | --- |
| `2632CB0..2632D81`, 209B | Complete constructor with ArRg magic `41725267` at14, primary vtable `4744DB0` at0 and secondary `4744DE8` at8. Actual non-RIP offsets/literals and control topology match the held old constructor; the new RIP targets are recorded explicitly. |
| `4744DB0[0]`, 8B | Sole actual primary slot selects actual wrapper `2632D90`. No adjacent slot was read. |
| `2632D90..2632DC4`, 52B | Preserves original receiver and incoming EDX mode. Unconditionally calls actual `2632DD0`; afterward modebit0 conditionally calls the known sized resource-release role with original receiver and size150h. Normal return yields original receiver. |
| `2632DD0..2632E3C`, 108B | Complete direct core. Rewrites primary/secondary vtables. Reads DATA pointer20; nonnull selects exact `EBA050(&ArRg20)`, then allocator30 virtual10 with `(allocator, DATA20, 8)`. On those ordinary returns writes pointer20=0, DWORD28=0. Both arms finally write14=`446C7464` and secondary8=`4744DF8`. |

The core does not directly write DATA count2C, physical Regi chunks,
Army association140 or Character148. This is a direct-instruction finding,
not a claim about the selected `EBA050` record callbacks. The nonnull path
uses the current allocator30 and rereads DATA20 after the cleanup returns.
The null path skips both selected calls and does not clear DWORD28.

The old complete93B `EBA050` cleanup is held at
`g2-background-round4-20261005/monthly-caller-effects/queue-consumer-source/first-removal-stage-ledger/later-manager-removal-stage/post-group-stage/`.
Its ordinary source loop captures signed vector+C count once; positive count
captures DATA pointer and dispatches stride16 records through each actual
slot0 with EDX0, then writes count0. Nonpositive count skips records and also
writes count0. This historical semantic source is reusable, but it is not yet
an actual4 function match or proof of the actual ArRg DATA record callbacks.
The actual4 core now supplies the concrete selected entrance needed to finish
that short source migration. No callee was expanded under the first377B plan.

```mermaid
flowchart TD
  A[Actual4 ArRg ctor2632CB0] --> V[Actual primary4744DB0 slot0]
  V --> W[Actual2632D90 receiver and mode wrapper]
  W --> C[Actual2632DD0 core]
  C --> H{Current DATA20 nonnull}
  H -->|null| T[Tag14 Dltd and secondary8 base vtable]
  H -->|nonnull| R[Actual reachedEBA050 ArRg plus20]
  R -. cached .3 loop needs actual4 mapping .-> U[Record slot0 with EDX0; count2C0]
  U -. actual record target inputs required .-> F[Allocator30 virtual10 DATA20 alignment8]
  F --> Z[Direct pointer20 zero and capacity28 zero]
  Z --> T
  T --> M{Wrapper saved mode bit0}
  M -->|set| S[Known sized resource release150h]
  M -->|clear| O[Return receiver]
  S --> O
  O -. current actual parent context required .-> N[Outer clear/invalidation and next raw cursor]
```

This is **research / direct-source closure**. Actual4 parent mode, DATA record
vtable/slot0 inputs and changed roster continuation remain separate. Native
source readiness does not grant a fixture, paused sample, next-date transition
or full daily/monthly loop. The independently implemented all30-phase supply
schedule in [the value-gap topic](army-future-date-value-gaps-12004.md) provides
date-selection input without waiting for complete detach replay.

Receipts: external `army-future-dates-12004/callback-map01/FAMILY-MAP.json`,
the two complete instruction details, and
`callback-map02/SELECTED-CORE-CAPTURE.json` / `SELECTED-CORE-108B.txt`.
Each records actual caches, exact edges and fresh-read accounting. No failed
capture or new capability RED occurred.
