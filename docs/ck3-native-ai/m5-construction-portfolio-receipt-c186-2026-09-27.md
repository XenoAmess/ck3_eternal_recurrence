# M5 construction portfolio receipt routing (2026-09-27 C186)

Scope: private M5 peacetime collector and construction source on the frozen
CK3 1.19.0.6 build (EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`).
The existing [observed opportunity dispatch](m5-observed-opportunity-dispatch-2026-09-23.md)
and [domain construction tree](domain-construction-ai.md) remain the policy and
native inputs. This note records a source routing change; no CK3 run is claimed.

The previous M5 collector and source read only `construction_ledger.applied`.
A second verified building overwrote that field, so a first building whose
completion watch or cold receipt was due no longer reached the formal consumer.
C187 reproduced the portfolio loss in the construction ledger path. The
existing R0237 scene contains one building and one marriage, so it is not a
two-building live proof.

The M5 collector now delegates receipt ordering to the construction
consumer's `priority_construction_receipt`: a pending action or due older
receipt goes through that consumer before any new joint proposal. The direct
peacetime source also refuses to publish a new proposal when a prior receipt
requires consumption. A verified older building that is not yet due does not
block a new native-legal positive-income building in another slot. The
resource selector still reserves one selected action on one frame; it does
not price construction completion or actual income from an opening receipt.

Focused source-path tests use two distinct construction requests: the first
is due for a 30-day check while the second is current. They require the first
request to be selected for independent readback and M5 proposal collection to
remain idle until then. Material completion, income effect and a new PID
recovery still require matching game evidence before expanding live claims.
