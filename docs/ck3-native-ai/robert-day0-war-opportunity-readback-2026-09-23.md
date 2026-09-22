# Robert day-zero war opportunity readback (2026-09-23)

The exact build is CK3 `1.19.0.6-steam23530548`, EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The native declaration and power decision tree is in [war-declaration.md](war-declaration.md);
the player's current narrow declaration gate is in
[player-war-entry-policy.md](player-war-entry-policy.md). This note records an
observation gap and an independent read-only entry, not a new war policy.

## Frozen evidence and actual gap

- [production-live] R0138 created an ordinary `xar_off` Robert checkpoint at
  `date_raw=53144328`, actor `29829`, episode
  `native-29829-2bc2d599f7f9`. The immutable source save SHA-256 is
  `77EAC299FA0619C88D6CCF55FC9C88980279376624C1A575C98FB22E09FCD6E3`;
  driver SHA-256 is
  `018077D3D53252D077CC29195562ECD79BED11AD760182E4EFFB606F5CB3B821`.
  The R0138 root snapshot's empty `declarable_wars` preceded a declaration
  query and therefore did **not** prove that no war was legal.
- [production-live] R0140 restored that save and completed four read-only
  turns at the same paused game date and native revision: one declaration
  query and three target power queries. Its persisted declaration result has
  nine final-legal rows across seven distinct target CharacterIDs. The
  observed targets `31899` and `37169` both resolved to effective defender
  `37169` with target/actor power ratio `1.52093`. Target `31549` has a
  final-legal `minor_religious_war` row and ratio `0.39892`. These are legal
  and strategic-power observations, not campaign-cost or victory proofs.
  The source artifact is the R0140 `formal-report.txt` and its paired
  `state/native-session/driver-state.json` under the authorized
  `m4-robert-slot43-20260923` asset root; those files stay unchanged.
- [static-confirmed] After a strong target assessment, the current production
  strategy exits its alternative-target read loop and applies only the
  `individual_county_de_jure_cb` conservative gate. `minor_religious_war`
  therefore remains `NO_DECLARE`. Extending a normal turn limit after the
  R0140 third assessment would reach a possible `life-advance`; it is not a
  bounded query-only path for the four unassessed targets `32725`, `33422`,
  `33621`, and `34320`.

## Independent read-only entry

`ck3_autonomous_player/native_bridge/research/run_war_opportunity_readback.py`
creates a separate prepared `ordinary_campaign_succession/xar_off` profile,
copies the frozen pair, applies the official `rebind_ordinary_seed_v1`, and
validates the cold checkpoint without launching CK3. The candidate manifest
pins the source and prepared pair, environment, exact EXE, DLL, injector and
operator. The owner must allocate a new round and pass the existing
`xar.ck3.single-instance-round-allocation/v1` ledger before `--live`.

Live mode calls only official MCP capability, snapshot, campaign-root,
declarable-war, and one-target war-entry-assessment tools. It queries each
distinct legal target up to an explicit bound, then verifies the same paused
snapshot, native command history, zero gameplay action and zero date advance.
If the target count exceeds the bound, the report is `green_partial` and
cannot claim a complete opportunity inventory. A failed read or unexpected
command is RED. This script does not issue `ck3_declare_war` or select a
religious-war strategy.

R0140's three power reads can guide priority, but a full seven-target
same-frame comparison requires a new bounded read of all seven in one paused
frame. The live readback has not run as of this note. If it reveals only
religious or other claims outside the existing safe gate, the next action is
to inspect the necessary war entry costs, participant commitments and exit
terms under the project's narrow war exception before proposing a typed
declaration. A power advantage alone does not authorize one.
