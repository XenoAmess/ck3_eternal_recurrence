# CK3 turn bundle v1

## Current status

- **[static-ready, live pending]** `ck3_query_turn_bundle_v1` is a public
  read-only MCP tool with response schema `xar.ck3.turn-bundle/v1`.
- It consumes one cached normalized state snapshot and exactly one existing
  `campaign-root-context-v1` query. Both inputs must share the same public and
  native revision, snapshot ID, date and paused frame.
- It already delivers truthful minimum alerts for ruler alive/landless state,
  direct-vassal and adjacent-holder presence, the primary title's first
  ordered successor, monthly income, current health and current domain
  size/limit. It also publishes the engine's current first heir for every
  personally held county-or-higher title and a split-partition alert. The full
  bundle stays `status=partial` and `readiness.ready=false` because council is
  not yet observed. The minimum targeting-faction
  alert is observed, while faction identity, power and deadlines remain open.
- This aggregation changes no native mailbox, DLL, game object or action path.
  Native AI decision-tree research is N/A because the package groups observed
  state and does not introduce a counter-policy.

## Tool contract

Tool: `ck3_query_turn_bundle_v1`

Input:

```json
{"expected_revision": 4}
```

The response contains six typed domains:

| Domain | Available now | Explicit gap |
|---|---|---|
| `ruler_state` | CharacterID, alive, primary title, capital, government, exact-build monthly income and health band, optional current gold and raw stress points | health treatment, disease/injury cause and prognosis |
| `realm_state` | top liege, independent state, direct landed-vassal IDs, adjacent Province-holder IDs and grouped top-liege IDs, native domain size/limit with derived available/over-limit counts, targeting-faction count and minimum threat boolean | holding identities/buildings/construction, council, faction identities/types/power/discontent/deadline |
| `succession_state` | ordered primary-title successor IDs, first primary-title heir, no-heir alert, and per-title current first-heir partition with split-risk state | succession law, claims, hypothetical distribution after law changes and post-death reconciliation |
| `pending_state` | current normalized event and pending character interaction, including proven absence | unavailable only when the source snapshot lacks that observation surface |
| `war_state` | sorted WarID, player side, primary opponent and relative score summaries | unavailable only when the source snapshot lacks `active_wars` |
| `alerts` | dead, landless, raw stress threshold, low-health threshold, direct-vassal absence, adjacent-holder presence, primary-title no-heir, partition split and targeting-faction threat | treatment and post-death reconciliation |

Every domain uses the common component shape:

```json
{
  "status": "available|unavailable|not_applicable",
  "value": null,
  "unavailable_reason": "..."
}
```

`not_applicable` is used only for a proven legal absence, such as no current
event, no pending interaction, no primary landed title, or a primary title with
no observed successor. Missing observation support remains `unavailable`.

## Alert and readiness meaning

`readiness.minimum_alerts_ready=true` currently means all three narrow domains
have an observed alert input:

- ruler: alive/dead and landed/landless;
- realm: direct landed-vassal and adjacent external holder presence;
- succession: primary title and its complete ordered successor vector.

It does not mean the G2-M1 acceptance gate is complete. `realm_domain_ready`
now means exact-build `GetDomainSize` and `GetDomainLimit` both produced valid
same-frame values; it does not claim holding identities, buildings,
construction or grace-period penalty state. The broader `readiness.ready`
remains false until the same-frame query can also supply council.
`succession_partition_ready=true` means the same campaign-root frame contains
the complete current first-heir projection for all personally held
county-or-higher titles. It does not claim law, claims or a hypothetical
distribution. `ruler_health_alert_ready=true` means `Character.GetHealth`
supplied signed Q100000 health and the bundle applied its frozen `1.5/3.0`
cutoffs; `raw < 300000` raises `ruler_health_below_fine`, while
`raw <= 150000` enters `dying_or_worse`. It does not claim treatment or death
probability. `realm_faction_alert_ready=true` means only that the
exact-build targeting-faction count and its nonzero alert are available; it
does not claim faction prioritization or response readiness. Monthly income is required in every
available campaign-root frame; current gold remains an optional
normalized-snapshot surface. `ruler_resources_ready` is true only when both are
available. Raw stress may be individually available without closing its larger
health/stress gate.

The raw stress alert uses `stress_points >= 100`. It reports the first CK3
stress-break threshold as a boolean and preserves the raw points; it is not a
health estimate or a complete stress-management policy.

## Binding and failure behavior

The aggregator rejects:

- any public/native revision, snapshot-ID, date or pause mismatch;
- disagreement between cached `played_character` and the campaign root;
- malformed or duplicate WarIDs;
- malformed relationship or successor identities;
- a landless root that invents title successors or partition rows;
- a partition row whose title, holder, tier, primary marker or first heir
  disagrees with the campaign-root contract.

If the underlying campaign-root query is typed unavailable, every bundle
domain becomes unavailable with the same reason and all readiness flags remain
false. A partial available bundle never fills missing fields from OCR, save
text, historical artifacts or another frame.

## Focused verification

- Contract fixtures cover successor order, high-stress, gold, exact-build
  monthly-income and health projection, health cutoff boundaries, domain
  size/limit projection and targeting-faction alert projection,
  adjacent holder-to-top-liege grouping, WarID sorting, landless and heirless
  `not_applicable`, root typed unavailable, missing optional surfaces and
  cross-frame/identity drift rejection, per-title split partition, barony
  exclusion and holder/primary-heir disagreement.
- Service integration reuses the already exact-bound campaign-root call.
- The official MCP SDK lists and calls `ck3_query_turn_bundle_v1`.
- The focused campaign-root/live-harness/turn-bundle suite passes `42/42` in
  normal and optimized modes; the native reader and source contract are
  independently executable and GREEN.

No CK3 process, recorder, injector, keyboard, mouse or foreground window was
used for this package. One future already-required paused G2 session should
sample the tool together with the campaign-root/entity-directory checks; a
dedicated long run is not required.

## Next observation package

The remaining M1 off-screen work is the bounded council reader described in
[council and development](council-and-development.md): incumbent identity,
stable task key, typed target and effective-seat fallback still need exact-build
closure before `realm_council_ready` can become true. Deeper faction
identity/power/deadline inputs belong to the later governance response package.
Each new field should enter this same bundle only after its native evidence and
focused fixture are complete.
