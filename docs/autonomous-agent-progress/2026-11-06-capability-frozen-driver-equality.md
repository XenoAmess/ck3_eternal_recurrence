# Avoid re-encoding the identical frozen Driver for equality

The capability input consumer rechecked its actual frozen Driver owner by encoding both the current and supplied complete Driver for byte equality. Both capture and still-current validation use that check, and readiness invokes the capability producer twice. The complete capability result cannot be cached: its actual runtime also performs dynamic owner, pending-child, option, status, source and file checks.

Only the pure Driver equality clause now has a narrow identity path. When both records hold the exact same immutable Complete object and its actor ID has the exact BigInteger class, identity establishes equal encoded bytes. All other objects and BigInteger subclasses retain the original two full encodings and their left-to-right order. Stamp and auxiliary equality still precede the clause, observation equality still follows it, and all capture/still-current, capability projection and dynamic validation calls remain.

The proof uses actual source: Known is a record with no custom Driver getter; Complete copies its history list, defensively clones stored Value bytes, and encodes only stored data. Extra record field accesses have no side effects. There is no cross-call result cache, new type, field or method.

Validation uses one necessary changed translation unit and independent source review. The first compiler invocation passed, producing two classes in 3.9330326 seconds; the earlier preparation metadata rejection launched no JVM and is retained separately. No mirrored behavior test or old green suite was rerun for this pure equality change.

This software candidate does not identify the entire roughly 84-second observation cost or prove an actual identity-path hit or speed improvement. Runtime adoption should share a real necessary clean boundary with the other prepared changes, followed by a complete measured window that includes recovery and waiting. Normal gameplay is not stopped for this candidate alone.
