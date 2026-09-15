# Faction gift mitigation paused-live harness v1

This reusable harness verifies one hash-bound faction gift candidate against an
already running, paused CK3 runtime. It never launches CK3 and is not wired into
the shared bridge, schema, MCP surface or CMake targets.

The runtime config must pin CK3 `1.19.0.6`, executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`,
the exact candidate manifest SHA-256, the candidate ID and commit, a portable
transport command, the Q100000 minimum gold reserve, `raw_first=true`,
`launch_ck3=false`, and retry policy
`forbid-same-candidate-after-submit-claim`. The candidate manifest also pins
every candidate file by relative path and SHA-256.

The transport reads one JSON request from stdin and receives `--step` with one
of these values:

1. `targeting` returns one paused targeting faction leader/member, full
   generation-bearing IDs, snapshot/date/native revision, player gold and the
   exact legal `gift_interaction` preview.
2. `gate` executes the FACTION13 read-only integration gate and returns READY
   with identical identities, revisions, resources, cost and reserve.
3. `submit` enters the FACTION10-12 one-shot action path. Its result must be
   only `submitted_verification_pending`; success or postcondition fields in an
   ACK are a typed RED.
4. `receipt` performs a fresh paused requery. The same faction, recipient
   opinion and player resources must prove the exact gold delta and
   `gift_opinion` value before `mitigated` or `left` can be GREEN.

For every step, the harness writes stdout and stderr byte-for-byte before JSON
parsing. Parse errors, nonzero transport exit, contract drift and failed
postconditions preserve those raw files and return a typed RED. Immediately
before `submit`, the harness exclusively creates a ledger keyed by the
candidate manifest hash. Once that ledger exists, the same candidate cannot be
submitted again, including after an invalid ACK or failed receipt.

The harness result distinguishes transport, targeting, gate, submit-ACK,
receipt, candidate-hash and retry REDs. A GREEN result records only a verified
`mitigated` or `left` receipt; it does not claim that the gift caused faction
dissolution or member departure.

Standalone verification:

```console
py research/test_faction_gift_mitigation_paused_live_harness.py
py -O research/test_faction_gift_mitigation_paused_live_harness.py
```
