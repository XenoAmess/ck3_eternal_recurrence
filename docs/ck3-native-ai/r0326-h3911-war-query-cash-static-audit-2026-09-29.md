# R0326 / H3911: selected war query and cash boundary

Status: **static audit only; no approved zero-fee observation**. This record
concerns the single selected `query-war-termination-options-16777231` step in
the R0326 source result. It does not price a later move, troop raise,
mercenary hire, pending commitment, future war cost, risk reserve, or minimum
treasury reserve. The #449 receiver has not produced a matching managed query
receipt from the H3911 pair.

## Exact inputs and scope

- H3911 paired DLL: `C:/Users/1/OneDrive/WAR/M5-WAR-CASH-20260928/R0321-runtime-xar_ck3_bridge.dll`, SHA-256
  `C71F6A5DFE8D23374B5B73F9DFA18AD9455CFF087D36EC93D2D29F7F610E8786`.
- CK3 1.19.0.6 executable: SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
  The bounded disassembly helper verified this entire file hash before decoding
  each RVA below. No full executable scan or game launch was performed.
- H3911 source manifest names commit
  `a6d1ae845f11e1e0bae79cac3fd9c30b00afae59`. `git diff` from that commit
  to this #449-based worktree shows no edit to the war-termination branch of
  `native_bridge/src/bridge.cpp` or the war-termination reader and interaction
  helpers in `native_bridge/src/ck3_11906.cpp`. It does show edits elsewhere in
  both files, so whole-file hashes of this worktree are **not** the source
  commit's binary provenance.
- The DLL contains the literal `query-war-termination-options-` three times.
  Literal presence and the manifest do **not** prove that the exact loaded
  binary dispatch reaches only the audited source branch. A disassembly or
  reproducible build audit of the exact DLL remains required.

## Actual request, treasury read, and mutations

| Boundary | Evidence | Conclusion |
| --- | --- | --- |
| Driver request | `native_driver.py:8090-8215`, `15976-16198` | `_execute_primitive_step` sends protocol `type=execute_step`, the exact step, `request_id`, and `expected_revision`. It captures the request/response envelope and owner ledger. This protocol type is shared by both queries and gameplay actions; the exact step and dispatch branch decide its effect. |
| Bridge dispatch | `bridge.cpp:16513-16628` | The exact query branch checks WarID and revision, reads admission/completion snapshots, calls `ReadWarTerminationOptions`, and emits a query result. There is no direct `submit_command` in this source branch. It increments `war_termination_query_sequence` after a successful write; a changed snapshot may invoke `PublishSnapshot` and reject. These are bridge bookkeeping mutations. |
| Native reader | `ck3_11906.cpp:17763-17891`, `6723-6817` | The reader resolves one active war, computes options, and for the war leader constructs temporary character-interaction contexts, validates them, reads acceptance and optionally evaluates a recipient answer. Source-level call tracing reaches game-native functions; it does not establish that every nested call is pure. |
| Snapshot treasury | `ck3_11906.cpp:10577-10582`, `game_contract.hpp:925-953` | Gold comes from the played character extension at `+0x100` as signed 64-bit raw at scale 100,000. `Snapshot::operator==` is defaulted over all members, including gold. Thus the bridge's admission/completion snapshot comparison detects a changed observed treasury value. It cannot rule out a transient debit followed by a credit, another side effect, or a later deferred command. |
| Driver cache | `native_driver.py:872-893`, `995-1018`, `2343-2350`, `16088-16192`, `27427` | `state.semantic_snapshot()` projects the last published `state_snapshot` held in `_semantic_snapshot`; `take_internal_semantic_snapshot()` does not request a fresh native `ReadSnapshot`. After postquery war identity and paused-frame checks, the driver updates `_war_termination_options`, query audit, and ledger. `_same_paused_native_frame` does not compare gold. The #449 receiver compares four outer/inner cached semantic projections for raw gold equality. This detects disagreement among published projections; the four reads are **not** four independent CK3 treasury measurements. |

The #449 receipt builder at
`war_cash_formal_query_runtime_receipt_v1.py:175-240` compares two outer
snapshots with the query wire audit's inner before/after projections. All four
come through the driver's cached semantic state. If no new `state_snapshot`
arrives, all four can repeat the same published value while the current CK3
treasury differs. The bridge's own admission and completion `ReadSnapshot`
calls are distinct direct native reads. Its source-level defaulted snapshot
equality includes gold, but the query response does not separately serialize
either native gold raw value. The receiver cannot independently inspect those
two values from its four cached projections. Even the bridge comparison
cannot exclude a transient debit followed by a credit between its reads, or
a deferred debit after completion. Consequently four-sample receiver equality
is a provenance and consistency check, not a native no-spend proof.

The exact EXE bounded disassembly confirms that native interaction evaluation
is **not memory-read-only** in the literal sense:

- `0x2C3F300` initializes fields of the supplied interaction context, including
  `+0x2D8`, `+0x2E0`, and `+0x330`; `0x2C3F380` releases and clears context
  allocations. The bridge supplies stack-owned context storage. These writes
  alone do not prove a game-state or cash mutation.
- `0xC569F0` constructs a war-resolution context and calls `0x2C3EE50` and
  `0xC56B80`; `0x2C3EE50` writes the supplied context's role fields. It also
  invokes other native functions, whose full side-effect closure has not been
  established by this bounded audit.
- `0x2C43F00` validation calls `0x2C42A30`, then potentially `0x2C43B40`.
  `0x2C43B40` calls `0x2C43220`, `0x2C43C50`, and conditionally `0x2C45300`.
  `0x2C44320` writes the acceptance score to its caller-supplied output and
  calls native score evaluation for a nontrivial context. The deeper calls
  can allocate or update diagnostic/cache state; the bounded trace cannot
  exclude game-state side effects or a gameplay submission in the complete
  transitive call graph. No direct call to the known `submit_command` RVA
  `0x0973E00` was found in the decoded top-level functions listed here. That
  is a narrow observation, **not** a no-submit proof.

## Promotion gate

The two approval registries in
`war_cash_termination_query_zero_fee_v1.py` remain empty. Before adding either
SHA, obtain all of the following for one exact #449 managed receiver run:

1. A query result whose selected step, WarID, paused snapshot, episode,
   native revision, request ID, and protocol response all agree. If actual
   #449 planning selects another step or no step, this candidate fails.
2. A loaded-process EXE/DLL/injector and source pair attestation, plus the
   official no-launch receipt and exact driver state binding. Disk path hashes
   alone do not attest mapped memory pages; report this limit.
3. An independent exact-DLL branch and native call audit with verified no
   gameplay `submit_command` reachability or a sufficiently narrow runtime
   no-submit observer. Record the actual scope of any cache or context writes.
4. Prove that the loaded DLL actually enforces the bridge's direct native
   admission/completion snapshot equality, including gold. The existing wire
   result does not expose the two native raw values; an independent value
   audit would require new native diagnostic fields or equivalent narrowly
   bound evidence. Separately verify one paused frame, equality of the four
   **cached** receiver gold projections, and an unchanged gameplay submission
   counter. A binary or runtime no-submit audit must cover effects that
   snapshot equality cannot see. Even all these checks cannot, by themselves,
   exclude transient debit/credit or deferred effects.

The current diagnostic producer deliberately returns `None` for the query
cost and all other four war cash fields until the exact receipts are promoted.
Even a later proven query cost of zero cannot make the joint wartime budget
complete while commitments, horizon costs, risk reserve, and policy reserve
remain unobserved.
