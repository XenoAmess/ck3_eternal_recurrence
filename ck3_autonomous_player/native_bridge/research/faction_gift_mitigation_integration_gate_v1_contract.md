# Faction gift mitigation integration gate v1

Status: `exact-build private read-only preflight`. This contract does not
publish a bridge or MCP capability and does not submit a CK3 command.

The gate composes four already versioned private layers:

- FACTION9 supplies an even-generation targeting-row publication containing
  full-generation faction, target, leader and member identities.
- FACTION10 defines the bounded gift request and pending-ACK/postcondition
  action contract.
- FACTION11 maps targeting rows plus same-frame faction, resource, opinion and
  gift-preview sources into that action observation.
- FACTION12 admits those callbacks only after the 1.19.0.6 executable SHA and
  all frozen generic-interaction RVA/address/span-hash anchors match.

One gate evaluation reads the targeting publication before and after two
independent source captures. READY requires identical publication generation,
proof epoch, row identities, snapshot/date, native revision, resources and
gift preview across the samples. The recipient must be the exact row leader
or character member requested, and the exact gift cost must leave the stated
minimum Q100000 gold reserve.

Any unavailable input or mismatch remains `red` with a typed bit and first
reason key. READY means only that a later owner may enter the one-shot action
path. It is neither a queue ACK nor proof that mitigation was applied. The
gate never calls native validation, idempotency claim or submit callbacks;
outcome still requires FACTION10 receipt verification against a fresh paused
requery of the same faction, player resources and recipient `gift_opinion`.
