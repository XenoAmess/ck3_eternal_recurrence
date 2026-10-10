# Actual4 Army pre-date prefix before original roster capture

The actual caller invokes `2A9A340(primary, full prospective CDate)` before
it captures its original Army roster. All557B of the actual direct callee are
now source-closed: it conditionally appends original primaryC8 IDs to primary158,
and does not directly change the primary50/5C roster or Army lifecycle fields.
The complete nonpositive-D4 arm has no state writes or calls. A minimal current
header observer and pure conditional classifier are authored for that arm.
Status is research/source implemented; the new focused test, production
integration and live observation remain unqualified.

CK3 is **1.20.0.4**, Steam build25734779, EXE SHA-256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
The existing actual-build identity is reused without rehashing or reading the
executable. The source checkout remains read-only; this topic and all candidate
files reside in the external continuation-44 package for Root integration.

## Actual source and invocation boundary

The already held `army-world-family/native-main/map01/pre_date_roster_source-DETAIL.json`
contains all1438 decoded actual4 caller bytes, full source-record SHA-256
`b5b83af9f477c57ee15d677487def10633f5df932f6524250c1328b174a56b7e`.
The external `SOURCE-ENTRY-LOCATOR.json` freezes only the relevant caller slice
and exact function-table row, with their identity and interpretation labels.

| Source location | Exact role |
| --- | --- |
| `2A99DC0` | Save actual outer secondary receiver RCX in R13 |
| `2A99DCA..2A99E60` | Keep actual GameState and construct the full prospective CDate64: copy current QWORD, wrap-add24 to raw low DWORD, compute the actual calendar roles using signed arithmetic and selected calendar tables |
| `2A99E66` | RDX is address of that full CDate at stack RBP140 |
| `2A99E6D` | RCX is R13-8, actual primary |
| `2A99E71` | Direct CALL2A9A340 |
| `2A99E76/E7A` | Only after return: capture original pointer at primary50 and signed count at primary5C |

Full CDate64 is the source argument. Raw+24 alone does not supply its upper
calendar bytes. The prospective argument is also distinct from a later
callback's retained date or GameState9C dispatch selector. This package does
not reconstruct either from a different source stage.

The NEW runtime function table contains ordinal146721, raw row
`[44671808,44671847,85261480]`: `[2A9A340,2A9A367)`,39B, unwind514FCA8.
This is only the first runtime fragment. It is not the callee's whole logic;
neighboring records are not combined without actual branch/chain proof.
`ROOT-PREFIX-CACHE-FIRST-REQUEST.json` preserved the initial request. Root has
now returned exactly39B, raw body SHA-256
`b850fb3da05c15c9fe8c2351ed67756bc2cb6e1df04ec40f07813d6bab78339a`.
All39B decode completely. This fragment reads sign-extended primaryD4 at34A,
keeps primary inRBX and the actual date pointer inR13, then branches at35A:
signed count<=0 goes to2A9A563; positive count falls through to360, whose
QWORD global5D1DE48 read ends exactly at367. The fragment directly writes
no game-state field. Its prolog/argument retention does not prove either
complete arm's effects.

Only those actual reached entries were queried in the held runtime table:
ordinal146722 `[2A9A367,2A9A563)`508B/unwind529D0C0 for the positive
fallthrough, ordinal146723 `[2A9A563,2A9A56D)`10B/unwind529D0E8 for the
explicit nonpositive branch. `ROOT-REACHED-CONTINUATION-REQUEST.json` requests
exact cache-first518B. `FIRST-FRAGMENT-SOURCE-EFFECTS.json` freezes the source,
full instructions/byte identity and branch-dependent metadata locators.
The neighboring records are used only because actual control-flow reaches
their entries; no whole-function or callee semantics is inferred yet.

## Required source stage

The indispensable entry is the actual primary state immediately before
`CALL2A9A340`, coupled to the full supplied CDate64 and invocation identity.
Queue contents, roster identity/order and lifecycle fields must be captured
at their source-defined stage. A standing paused Army query may observe useful
current operands; it cannot recover the original pre-call roster merely by
sharing a receiver identity. The original Army list read atE76/E7A is itself
post-prefix, and later pending/assault/bucket/persistent stages are distinct.

Continuation-33 owns later persistent preparation,35 owns later assault inputs,
41 owns post-date. Shared production core/wire/driver/Service/CMake/report
integration and all game work remain Root's.

## Complete positive branch and actual stores

Root returned exactly the two reached508B/10B fragments. Their raw SHA-256s
are `b15ce0017b934332ebec4ecead323c25518ceae3575849d545f52bb613a59818`
and `65ab867f5330a449f4fb9f96bbff2a90ea98a8c1d6027e70f57bdf8d42e01ed0`.
All557B decode, all direct branches remain within these proven spans, and the
actual normal return is2A9A56C. Their concatenation has SHA-256
`5f524389014c4f58d908bc9d06d0952be0c7590990af06179905fcb4a7036b11`;
this is a constructed hash of the three retained fragments, with no extra
whole-body binary copy. `COMPLETE-DIRECT-SOURCE-EFFECTS.json` and
`COMPLETE-PREFIX.actual4.asm.txt` freeze the reviewed source and direct tree.

1. Positive initial signedD4 is kept inR12. The loop retains every index,
   including repeated IDs; it never clears source countD4 or pointerC8.
2. Use actual Army registry5D1DE48 or fallback5D1DE50. Registry lookup uses
   low24 unsigned bounds, slot16+8, nonnull pointer and complete requested
   DWORD comparison atArmy10. There is no separate Army magic or sentinel
   admission check in this prefix. When registry is null, the initial source
   ID read is skipped; a selected append still reads its originalC8 DWORD.
3. Use selected Army128 to resolve actual Combat through5D1DE70 or fallback
   5D1DE18. A Comb tag at0C and own fullID8!=FFFFFFFF skips the row. The
   fallback's own fields are preserved rather than forced invalid.
4. Otherwise, signed Army5C<=0 skips. Positive Army5C scans the Army50 array
   of QWORD pointers in order. Each pointed object contributes its signed
   DWORD0 date head; their object type is not inferred. Full supplied CDate64
   is loaded at42A, and its low32 is used in the signed comparison. The first
   date head<=that raw date selects one append, then stops this row's scan.
   All heads greater than the supplied date select no append.
5. Append the raw source primaryC8[index] DWORD, including generation bits;
   it is not replaced by the selected fallback Army's own ID. With count164
   unequal to capacity160, write destination158[count164] then wrap-increment
   count164 at530/533. Source order and every repeated occurrence are retained.
6. Equal count/capacity selects growth. Allocate a new buffer, write the new
   ID at oldcount, copy every positive oldcount previous DWORD in order, free
   the old buffer, then write160 capacity,158 pointer and164 count+1 at506,
   513 and51A. Negative counts are not normalized into empty valid vectors.

The only calls are allocator primary168's actual vtable+8 at49C and+10 at4FC.
Allocation receives zero-extended newcapacity times4 bytes and alignment4;
free receives old158 and alignment4. There is no direct Army lifecycle,
removal or commander callback. This proves the direct footprint, not arbitrary
loaded allocator target semantics or absence of physical overlap. A physical
replay must retain actual allocator targets and input/output address aliases.

The growth expression is signed max of wrap32(oldcount+1) and the hardware
binary32 conversion/multiply/truncate of capacity160 with the actual factor.
After Root delegated finite acquisition, the existing mapper and D shared
cache acquired only the source-selected literal49F64F0..F4:4B,
hex0000C03F, bits3FC00000, value1.5, SHA-256
`c0e336a5f371ef22cd534e094269f2c1a9635cd080b71ffa671086832d3b60b7`.
`ACTUAL4-GROWTH-FACTOR.json` binds actual MOVSS2A9A37F and the capture policy;
no guessed constant, EXE rehash, section scan or old-image read occurred.

Direct writes touch only primary158/160/164 and the destination DATA. They
do not directly touch primary50/5C, primaryC8/D4, Army or Combat fields, or
the supplied date. Destination memory aliases and indirect allocator effects
remain distinct physical input dependencies; an empty direct intersection
must not be promoted to a complete historical roster-preservation observation.

## Minimal conditional header leaf and integration seam

`army_pre_date_prefix_stage_12004.hpp/.cpp` observes only signed rawprimaryD4
through an injected readonly reader and actual primary identity. It binds the
exact4 SHA, keeps failed reads absent, and never retries or invents zero. The
pure classifier proves the complete no-work arm for<=0 without demanding date,
source IDs, destination queue, Army, Combat or roster reads. Positive counts
remain independently readable but require the ordered positive-stage inputs.
The projection always keeps historical_invocation_reconstructed=false.

The existing Army query's FirstRemovalCleanup captures currentC8/158 ordered
lists at `ck3_12002_army.cpp:710`, under the actual4 binder. Its ordered list
does not transport rawD4; list length or empty output must not be presented as
an observed raw zero. Root can reuse the already performed same-query header
read when exposing the raw signed count, then call this pure classifier; the
standalone4B observer is a fallback primitive, not a second endpoint. Current
header identity/date/frame remains separate from the original invocation entry.

`army_pre_date_prefix_stage_12004_test.cpp` authors nine synthetic cases for
zero, negative/INT_MIN, positive/INT_MAX, failed read, wrong build, missing
primary and address overflow. They require only one4B demanded read and no
historical reconstruction claim. `FOCUSED-ARGV.json` preserves the one new
standalone build/run request. At this delivery it is **NOTRUN**; source
authoring and record validation do not qualify a production provider.

Remaining positive construction is concrete: original pre-call primaryC8/D4,
the full actual supplied CDate64, source-ordered Army/Combat resolutions and
Army50 date-head frames, initial158/160/164 queue contents, and actual growth
allocator/alias identities. Dynamic rows must reflect earlier selected writes;
standing current query rows cannot backfill the original CALL. Root owns the
same-query production API and later stage integration. No game operation or
old FIRST replay occurred. Source acquisition is Root557B code plus owner4B
literal; record checks verify structure/byte integrity without live credit.
