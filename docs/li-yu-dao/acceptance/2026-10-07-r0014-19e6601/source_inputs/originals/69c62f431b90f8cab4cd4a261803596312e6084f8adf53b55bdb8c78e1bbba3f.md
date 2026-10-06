# Serialized numeric values observed during R14 I3b proposal

Two stored numeric forms blocked the B1 formal reader while the original checkpoint parser and typed identity reader remained correct. The change is limited to `number()`; saved rows, parser output, entity IDs, original save bytes, and phase/ownership checks remain unchanged.

An explicit present `type=value` row with no identity and a data block containing exactly the `type=value` entry represents numeric zero. A missing variable, absent row, wrong type, empty block, identity entry, or additional data entry is not defaulted to zero. The owner row expiry tick is retained separately.

Explicit identities are fixed-point signed64 values at scale 100000. CK3 serialized B1 pending vote -1 as the unsigned bit pattern 18446744073709451616. `number()` decodes the high bit as signed64, divides by 100000, and requires an integral result. Signed/unsigned overflow, a wrong scale, malformed identity, fractional high-bit values, and entity/reference types are rejected. Reference identity readers do not use this signed numeric conversion.

The two small fixtures are exact extracted saved-row shapes from R14 B1, not complete save bodies. Their original checkpoint SHA is retained in each fixture. Nine explicit-zero tests and five signed-value tests passed against external reader003; their original receipts are preserved. The existing 20 reader tests are separately run against that exact candidate in an external mirror with unchanged test logic, dependencies and raw parser. These checks provide reader compatibility evidence; native query and formal mandate credit remain separate actual evidence.

Apply only after normal game exit, helper closure and screen CAS release. While R14 runs at clean HEAD19, the main reader, executable and build inputs remain unchanged. Failed B1 reader001/002 and the earlier failed manifest author attempt remain preserved externally.
