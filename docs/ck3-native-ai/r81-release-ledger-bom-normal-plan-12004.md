# R81 ordinary plan: actual release ledger BOM consumption failure

Status: the repaired ordinary planning branch was traversed live in HOT05.
The new ordinary release ACK is pending; the two authorized responses below
do not contain an independent release material result. The source-ready
baseline and original failure are retained below. Root owns fixture
qualification, actual ordinary execution and later receipt adoption.

Root's normal `ck3_auto_turn` attempt014 failed at
**2026-10-09 05:03:44.866667–05:04:07.662633 UTC** with FastMCP text:
`Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)`.
The saved response has no structured body and STDERR has no traceback.
The original failed response remains under
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261009/managed-full-h9715-saved6010-r81-native46restore01/operator/gameplay-responses/014-r81-after-save-normal-turn03.json`.

The finite current-source path is Service's ordinary planning call to
`plan_release_formal`, which reads `read_release_ledger(state_dir)` before
release material arbitration. At source
`088fed39e0ceda7b28c2b0ee2113db4ce61fa58a`, the reader applies
`json.loads(path.read_text(encoding="utf-8"))` to
`player-prisoner-release-formal-v1.json`. The direct normal entry is at
`bridge/service.py:1883`, with the war and initial-plan entries calling the
same function. The decoder fails before the ledger shape or pending identity
can be interpreted.

One three-byte read of the actual **44,935-byte** file proved prefix
**`EF BB BF`** at
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261009/g2-robert-mainline-12004-full-h9715-saved6010-r81-native46restore01/state/player-prisoner-release-formal-v1.json`.
This is direct byte evidence for the same decoder failure in the current
ordinary path. The worker did not deserialize the opaque actual record,
inspect a large driver file, survey other ledgers or query the live game.
The sole fixture below completes the production-consumer reproduction.

The minimum repair changes only that release reader's encoding to
`utf-8-sig`. It accepts the actual BOM while continuing to accept existing
plain UTF-8 files. It does not change JSON schema, prisoner state, native code,
ACK admission or writer behavior. Historical bytes and the failed attempt are
retained; there is no BOM stripping or state-file rewrite.

Root's only new qualification node is
`test_r81_release_ledger_bom_normal_consumer.py::test_actual_r81_bom_release_ledger_is_consumed_by_normal_plan`.
It reads this actual small capture once, reproduces the old decoder's precise
JSON error, copies the bytes privately, and invokes the real release reader
and normal release planner. Its paused frame is an explicit synthetic seam;
it performs no native query or action. The production-consumed record must
match the decoded saved record, and the private copy must remain byte-for-byte
unchanged. No old GREEN fixture is rerun. Worker test/import/build/hash/Game,
SDK calls and capability credit are zero. Live recovery remains pending Root.

## Root HOT05 actual ordinary traversal and pending release (2026-10-09)

This documentation-only association uses independent source base
`e5fd088cde640b0a1ea29ff40888af95d9300c95`. Each of the two authorized
responses was read once: [ordinary005](Z:/ck3_mod_rewrite_process_assets/g2-background-20261009/r81-sdk-process-time-hot05/operator/gameplay-responses/005-r81-timefixed-normal-turn04.json)
(141,054 B) and [following006](Z:/ck3_mod_rewrite_process_assets/g2-background-20261009/r81-sdk-process-time-hot05/operator/gameplay-responses/006-r81-normal-release-receipt01.json)
(146,688 B). No Driver or save was read, no production ledger was rewritten,
and no Game, SDK, CIM, EXE, hash, build or test operation was performed here.
The first semantic stdout exceeded its display budget; the narrower prisoner
record was derived from the already-saved extraction, without rereading either
original response.

Root's ordinary005 ran at **05:51:50.663805–05:52:23.771861 UTC**, taking
**33.108056 s**. Its structured result is `executed`, and its selected step is
`submit-player-prisoner-release-v1`. This is the normal scheduler's selection,
with deferred route-contact work recorded in the plan. It proves the repaired
release-ledger decoding/planning branch was reached in actual operation; it
is not a standalone forced release or a replay of a historical request.

The current complete custody collection has one row: ordinal0, full target
**54235**, owner/jailer **29829**, with `custody_relation_verified=true`.
The native collection is revision6 at raw53288568, query sequence2 and
proof512916; its transport provenance records public queried revision2 and
native queried revision6. The preview's legacy `public_revision` field is6,
so that label must not replace the transport's actual public revision2.
The native two-role definition is `release_from_prison_interaction`, runtime
ordinal186/hash3627454604, with actor29829, recipient54235 and
`puppet_or_actor_character_id=29829`. All thirteen selectable flags are off:
selected keys `[]`, mask0, `can_send=true`, final context/readiness true and
`auto_accept=true`/`would_accept_now=true`.

All ten quoted entries are raw0 at scale100000, actor payer, `on_send`:
gold, prestige, piety, renown, influence, herd, treasury, treasury_or_gold,
merit and barter_goods. The ransom preview is typed unavailable with
`role_unavailable`; this does not fabricate a zero-value ransom offer.
The same-frame claim-CB war100663329 read has empty release pairs and its own
complete/stable scan flags. That is a current narrow retention input, not a
statement that every possible cost or war consequence is zero.

The new action request is
**`prisoner-release-f62b0fb089394694ab72e2db8ec1efca`**. Its actual4 action ACK
preserves player29829/target54235, pre-native6/raw53288568, sequence2,
all-off mask0, the ten zero quotes and auto-accept. Its status is
`submitted_verification_pending` and `material_result=false`.

Following006 still publishes `prisoner_release_pending.stage=receipt_pending`
with that exact original ACK and `material_result=false`. Its ransom
observation is unavailable with `prisoner collection identity drifted`.
The actual ordinary selected step is the deferred route-contact horizon,
ending at **native snapshot9/public revision5**, raw53288592, from
raw53288568: one actual game day. This following response does not report
that54235 is free, a retained-target custody result, a consumed release
receipt or a release relation change. The typed unavailable observation is
retained as an observed result; it is not relabelled a successful receipt.

Neither authorized response publishes a current retained material or keeper
opinion object. `target_opinion_of_actor` would mean **54235 → 29829**, and
the named `released_from_prison` modifier belongs to that same direction;
`actor_opinion_of_target` would mean **29829 → 54235**. No old R80 opinion
baseline is substituted for a missing current before/after object, and no
delta, named gain, release cause or actual resource debit is inferred from
the quoted zero costs or the ACK.

This adds actual ordinary branch traversal, one fresh pending ACK and its
one-day following. It does not close full M6 or an independent release
material/cost/causation result. The prior actual M4 input join excludes54235
from both targeting factions' full Character member vectors, and the prior
complete direct-landed list also excludes it. This release must not borrow
M4 vassal/faction benefit from the unrelated33435 opportunity.

Root owns the next ordinary independent receipt, same full target/custody
and direction-correct material query, receipt consumption and matched cold
evidence. The original BOM attempt014 remains unchanged at its original
path. No source or ledger implementation is modified by this appendix.
[Thin actual association and Oct9/W41 fields](Z:/ck3_mod_rewrite_process_assets/g2-background-20261009/r81-release-bom-normal-actual-association/ROOT-DELIVERY.json)
record this bounded result and pending work.
