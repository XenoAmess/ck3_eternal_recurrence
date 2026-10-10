# Actual 1.20.0.4 conception normal close-family producer

The directed input is `ConceptionPairProviderInputs12004.normal_close_family`,
an `optional<bool>` read from the existing qualified native `FamilyPredicate`
at `kFamilyCloseFamilyRva = 0x2912080`. No new body capture, qualification or
old family matrix is required for this producer.

The retained actual caller sets RDX to second/R13 at `0x2B962CA`, RCX to
first/R14 at `0x2B962CD`, calls the getter at `0x2B962D0`, and tests AL at
`0x2B962D5`. A true result takes the current QWORD multiplier at `0x5C69DF0`.
A false result continues to the distinct `0x2912210` related predicate.
That predicate's result cannot supply this field. The caller's held span is
`[0x2B95670,0x2B96595)`, SHA-256
`ed8e19f51650aa5a2d778ed4b4a2ee016505b5e8ba4b5f0503e26594fda1caf0`.
`SOURCE-REUSE-FREEZE.json` retains the necessary caller instructions and
the hashes of the qualified typed ABI inputs.

The leaf header is
`candidate/include/xar_bridge/conception_normal_close_family_12004.hpp`.
All API names are in `xar::ck3_12004`:

```cpp
auto bindings = BindConceptionNormalCloseFamily12004(
    image_base, executable_sha256, guarded_read_memory, read_context);
auto observation = ReadConceptionNormalCloseFamilyForPair12004(
    bindings, first, first_full_id, second, second_full_id,
    first_selects_alternate, second_selects_alternate);
full_inputs.normal_close_family = observation.normal_close_family;
```

The binder reuses `BindFamilyBreakPenaltyImage` and selects only its already
qualified `close_family` callback. It does not run the penalty reader or any
other getter in that binding object. The native ABI remains
`ck3_12002::family_break_penalty::FamilyPredicate = bool (*)(void *, void *)`.
The bool records the caller's tested branch value; no raw numeric AL contract
is introduced.

Receiver pointers and full IDs come from 55's existing same-query household
resolution. The reader copies each receiver's full generation-bearing ID at
`+0x18` before and after the directed native call. Missing identities, generation
mismatches, read failures and native getter failures leave the provider input
empty. A returned false is an available false. If a post-call guard fails,
`native_return_value` retains the raw typed return for diagnostics while
`normal_close_family` stays empty. Native invocation uses the existing Windows
MSVC SEH boundary pattern; portable fixtures cover C++ exceptions rather than
claiming Windows hardware-fault coverage.

Selector demand follows the actual source order. First true skips this getter
without demanding second. Missing first remains unavailable even if second is
true. First false then second true also skips the getter. Only both observed
false demand the getter. The skipped result is `status = not_required`, with
the explicit first/second skip reason and no bool or ID samples. The provider
uses its alternate route and does not demand this empty normal-route input.

`same-query-producer-49b.patch` is a concrete companion diff against 55's
retained DTO, collector, JSON serializer and Python decoder. It inserts one
binding per query and one reader per existing heir/spouse pair, serializes the
independent observation, and permits `not_required` only for this new decoder
field. `provider-input-mapping-49b.inc` shows the exact 17b assignment. All
shared candidate files and Z source remain unchanged by this package. Their
read-only hashes are in `COMPANION-CONTEXT.json`.

Validation belongs to the new central17b 10-case compound run. Its reader
assertions should cover directed argument order and observed false, both skip
routes, missing first with true second, stale generation causing no getter
call, and changed post-call generation retaining only the diagnostic return.
No separate focus, old 15-case child-limit test, full family matrix or game
query has been run by 49b. Root owns final integration and cold loading.

This bounded package is an active integration input. Its storage receipts use
the common policy, record actual local capacity, and set a 180-day review
deadline. Review or retire the candidate after Root confirms integration;
the source-reuse and delivery records retain their dated audit purpose.
