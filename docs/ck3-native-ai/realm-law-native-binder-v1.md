# CK3 1.19.0.6 realm-law native binder v1

Status: `static-ready private binder; native mutation ABI and paused live
receipt pending`.

This binder is fixed to CK3 `1.19.0.6` and executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
Its semantic inputs are the LAW3
`realm_law_governance_source_adapter_v1` snapshot and the LAW4
`realm_law_enact_action_v1` action contract.

## Evidence boundary

The frozen evidence in
`laws-contracts-and-succession.md` and
`g2_nonreligious_law_contract_succession_native_tree_v1.json` proves the
`GuiLaw.Enact`, `GuiLaw.GetCanEnactDescription`, law-group, cost and succession
reflection surfaces. It explicitly does **not** identify a safe legality
evaluator address, mutation routine, command serializer, calling convention,
object layout or command lifetime. Consequently this work package defines no
RVA, offset, byte signature or default production operation.

`RealmLawNativeBinderOperationsV1` is an injected table. A future exact-build
adapter may populate it only after the missing native targets and calling
conventions have been reviewed. Binding requires a complete table plus a
runtime signature-manifest SHA-256. The binder reads that proof twice before
attachment and rechecks the executable hash, module base, signature manifest,
signature generation, connection generation, current application-main thread
and paused state around every native callback. Tests supply an explicitly
labelled offline fixture operation table; that fixture is not native-address or
live-game evidence.

## Transaction

1. LAW3 resolves the played character, law container and every group for each
   of its two source samples. The binder checks runtime generation and proof
   before and after each callback; LAW3 then requires equal pointer-free
   values and an equal paused frame.
2. The binder reads resources with the same public/native revision, proof
   epoch, date and full player identity as the completed LAW3 snapshot.
3. LAW4 captures that combined observation twice. It accepts only an unchanged
   target group authority gate, engine-final legality and costs, succession
   shape, title-successor baseline and resource vector covered by the request
   budget.
4. Immediately before native submit, the binder captures the combination a
   third time and compares the selected target, resources and succession data
   with LAW4's pointer-free submission. It calls `submit_enact` at most once.
5. `submitted` and `submitted_outcome_unknown` both yield only
   `submitted_verification_pending`. A proof failure after possible handoff is
   retained as a pending ACK and makes later receipt capture fail closed; it is
   never rewritten as a pre-submit rejection or enactment success.
6. A later paused receipt capture reruns LAW3 plus the resource reader. LAW4
   reports `enacted` only when the requested law is effective, each resource
   delta equals the frozen engine-final charge, and the succession shape still
   matches. A pre-submit rejection maps to `rejected`; missing or contradictory
   postconditions map to `failed`.

## Remaining integration and acceptance

The binder, LAW3 and LAW4 are private and absent from shared CMake, bridge,
schema and MCP registration. The next native-evidence package must freeze the
actual evaluator, command construction/ownership, submit and resource-reader
targets for the exact executable, publish their signature-manifest digest, and
provide the injected operation table without weakening these gates. Shared
glue must then schedule enact and later receipt on the application-main thread.

Production acceptance still requires a real paused CK3 artifact showing one
eligible enact request, a verification-pending ACK, and a later receipt with
the effective law, charged resources and succession shape. Until that exists,
this component is not `fixture-live` or `production-live primitive`.
