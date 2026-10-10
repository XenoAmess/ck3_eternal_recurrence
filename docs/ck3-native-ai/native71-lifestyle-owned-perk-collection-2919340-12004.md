# Actual 1.20.0.4 Lifestyle owned-perk collection input

The selected-perk predicate at `31EBE50` calls `2919340` with the resolved
Character in RCX, then passes its RAX collection to `A11CC0`. The membership key
is the full QWORD Perk identity stored in the caller's stack slot. The initial
call is at `31EBE8F`, followed by membership at `31EBE9E`. Each prerequisite
independently calls the getter at `31EBF78`, then membership at `31EBF87`.
The initial result or collection identity must not replace those later demands.

The actual getter's complete 124-byte source is retained in
`shared-span-cache/new-02919340-029193BC.bin`, SHA-256
`9342d1832a22ea331c11692bd81c2dcda4f5650b7f771684314ae8e283a82188`.
The external `continuation-36c/SOURCE-2919340.json` records the literal decode
before this implementation. Existing actual Faith profile operands independently
name Character extension `1B0` and its actual-perks collection `220`. No new
executable acquisition or source capture was needed.

`ReadLifestyleOwnedPerkCollection291934012004` uses 16's shared readonly Access
and owns each copied operand in its result. A nonnull Character+1B0 pointer
returns the literal extension+220 identity without reading TLS, a collection
header or its entries. Returned address arithmetic preserves native 64-bit ADD/LEA
bits. An address in this DTO is a scalar identity; no borrowed object escapes.

For a null extension, actual `2919350` first reads the application's current
thread GS58 TLS-array identity. The caller supplies that captured raw identity
in `Access.current_thread_tls_array_identity`; the reader does not obtain it
from its worker thread. It then reads array[0], signed epoch at TLS0+10, and
signed guard at module+5D67FDC, in source order. Guard<=epoch closes the fast
return of module+54E78B8. Missing TLS, unreadable operands or the signed
guard>epoch slow path leave the return identity unavailable while retaining
the copied prefix. The slow path reaches `4223A84` and may reach `4223F24`/`4223A24`;
this reader performs none of their initialization or synchronization effects.
It never assumes that a null extension means an empty collection.

62c owns the full selected-perk predicate. For each initial/prerequisite demand,
it calls this getter reader afresh and, only when its optional return identity
is available, passes that identity and the literal Perk QWORD to 27c's retained
`ReadConstructionCollectionPredicateA11CC0V1`. That source-closed child copies
signed countC, pointer-stride8 entries and reloaded header operands, preserving
the final native endpoint comparison. The M5 caller uses its existing 512-entry
bound. Negative counts, excessive counts or failed copies remain unknown. This
leaf adds no membership algorithm and does not turn any membership result into
a complete CanSelect result.

The new case fragment has no main. 16's sole new selected-perk compound may call
`RunLifestyleOwnedPerkCollection2919340NewCases12004` once through central 10.
It supplies offline raw memory for extension-only reads, fresh repeated getter
demands, native return-bit wrap, the signed TLS fast path, missing TLS, the
unmodeled slow path and a failed epoch read that skips later operands. These
cases do not execute a getter, initializer, membership routine or CK3 process.
Source preparation is not a compile or fixture result.

The external 36c allowance is 4MiB inside Root's existing parallel 20GiB cap,
expiring with its current manual admission. The common storage policy applies:
active inputs receive a seven-day review, records a 180-day review, and derived
outputs a 48-hour review after actual close or last use. Shared source caches
are referenced directly and have no duplicate payload in this package.
