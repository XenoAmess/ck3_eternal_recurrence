# Current create final piety source model — 1.20.0.4

Status: **SOURCE CLOSED, CANDIDATE AUTHORED, NOT COMPILED OR RUN**.

`ReadCreatePietyFinalPriceSourceModel12004` joins the existing create base-price reader with the newly closed actual `2C628A0` Rite term and `2C4D660` actor-property term. It can return a known signed Q64 final amount when every reached source projection succeeds. It preserves the existing native getter as an independent observation and adds no mailbox key, public DTO field or endpoint.

The source/API freeze precedes this header: `CURRENT-PRICE-PARENT-SOURCE-API-FREEZE.json`, SHA-256 `7d829f1c51b4c146804f9f8da4fce39fcdb6248cabd9b68fe061cf4673758fd5`. Its 22 pins identify the exact direct dependencies and their source/qualification receipts. The sole new executable-body acquisition by owner49 is the 361-byte `[2C62CC0,2C62E29)` span, raw SHA-256 `bb68340a187385a3e8803b1ef8c6ca1573727e9e6ef91e37d0167fae60926c43`. The 1054-byte Rite term and 573-byte property term are reused from owners03 and20.

The selected native path is false-edit, mode zero and detail null in `2C64BB0`. Its sequence is:

1. `2C64C13` calls `2C641E0` with the original Rite and price payload. The existing dynamic create reader preserves both ordered QWORD collections, occurrences and concrete child failures.
2. `2C64D05` selects the actor modifier collection through actual `28C3AC0`. `2C64D27` reads key **`0x223`**, mode zero, scale `100000` through actual `2C4D660`.
3. `2C64D2F` adds the base and property result with low-64-bit wrapping. This wrapped signed Q64 enters `2C62CC0` at `2C64D46`.
4. `2C62D04` reads the actual `2C628A0` Rite term. Definition `+7C == 0` returns zero. With expression `+70 == null`, flag `+7B == 0` returns zero; otherwise signed Q64 `+68` supplies the literal term. These numerical paths do not require unconsumed actor/Rite/key/name/constructor fields. A reached dynamic expression preserves its concrete missing virtual-return reason.
5. `2C62D35` independently selects the actor collection again. `2C62D56` reads key **`0x224`**, mode zero, scale `100000`. The parent does not reuse or require equality with the earlier collection selection.
6. The frozen final-arithmetic projection applies the native negative-base clamp, wrapped factor, exact small/split multiplication path and final negative-result clamp. A negative or zero entered base still reaches the two child terms.

Both actor reads use the existing46c raw full-ID receiver entry and immediate post-term lifetime/source check. All 32 ID bits are preserved. `FFFFFFFF` requires an explicitly source-qualified original fallback receiver; this leaf does not resolve a CharacterDB fallback or read an invented receiver. The read adapter uses the same common guarded access as the base and term readers and makes no native call. Those additional recopy checks are software guards, not a claim about the original function's execution.

The result retains the original payload, actor, Rite, full-ID and full64 revision carriers; the create child; both independent collection selections and property results; the Rite child; the wrapped entered sum; and the final arithmetic diagnostics. It stops at the first reached unavailable child and leaves the final optional amount absent. Earlier copied results remain diagnostic inputs, not a substituted final quote. `actual_original_consumed_values` remains false.

The owning future application-thread collector must supply a stable valid receiver/draft/Rite frame and associate the carriers with its actual query. Revision alone does not prove freshness. The Rite full ID is a caller carrier on numerical paths which do not consume Rite fields. No current packet, observed native price, affordability, resource debit or complete legal decision is claimed here.

The old static24 and dynamic21 receipts remain frozen and are reused for their exact unchanged production inputs. New03, new20, final arithmetic, this parent and the separately authored offline40 tag-demand correction are not qualified by those old receipts. There are no application imports, builds, tests, native calls, Game/RPC/Steam operations, Z writes or Git operations in this work package. A future once-new connected qualification needs exact10 execution admission and the final current dependency recipe; old cases must not be replayed.

Review/protection expiry remains `2026-10-11T08:41:22.843427Z`; no new reservation or expiry extension was made. Keep the small source contracts and exact candidate pins while Root reviews this join. Follow the shared storage policy for later review and reclamation; this topic creates no permanent exception.
