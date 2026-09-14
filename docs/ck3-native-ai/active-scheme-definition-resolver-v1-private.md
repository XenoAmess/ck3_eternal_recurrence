# Active scheme definition resolver v1 private contract

Status: **static-ready private component** for CK3 `1.19.0.6`. This work
package does not add shared bridge/CMake/schema/MCP glue and did not attach to
or start CK3. A paused production snapshot and the shared heartbeat remain
required before this can be called production-live.

## Frozen input and exact-build evidence

The admitted executable is `binaries/ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The machine-readable evidence and verifier are
`active_scheme_definition_resolver_1_19_0_6_abi.json` and
`verify_active_scheme_definition_resolver_1_19_0_6_abi.py`.

The stock interaction source fixes the only supported mappings:

| Stable interaction key | Scheme type | Murmur3 x86/32 seed-0 hash |
|---|---|---:|
| `sway_interaction` | `sway` | `0x5783F850` |
| `start_murder_interaction` | `murder` | `0xDF3F9819` |

The native route is the original getter at RVA `0x831890`, stable-key hash at
`0x3B8B000`, and loaded database lookup at `0x997930`. The original caller
span `0x2C46E40..0x2C47020` proves that order and ABI. Lookup owns its database
lock. The private adapter must call it and must not traverse its hash table.
The singleton and miss/fallback slots are `module+0x570C100` and
`module+0x570C628`.

The exact enumeration reference proves only rows at database `+0x68`, signed
count at `+0x74`, and pointer stride 8. It does not prove a capacity field, so
the resolver uses a strict `1..4096` count bound and does not claim or read
one. Each definition must round-trip through the primary vptr
`module+0x4403CE0`, secondary vptr at object `+0x2A80` equal to
`module+0x4403CA8`, stable hash at `+0x14`, and canonical MSVC string at
`+0x18`. The database must contain exactly one canonical-key match and the
native lookup result must be that same pointer. This extra string check is
required because the native lookup compares the 32-bit hash.

## Lease and lifecycle

Every resolve requires the application main thread, a paused frame, and one
nonzero proof epoch. It performs this sequence twice:

1. Reread the singleton slot, then invoke the getter and require equality.
2. Invoke the native stable-key hash and require the frozen key/hash mapping.
3. Invoke the native loaded lookup, reject null and the current fallback.
4. Reread rows/count and every definition identity, require one exact key and
   require its pointer to equal the native lookup result.
5. Reread the fallback and capture the frame, requiring all values and the
   topology fingerprint to remain unchanged.

SCHEME6 independently resolves the returned interaction lease again inside
its command transaction. The resolver state stores callbacks and upstream
context only; it never caches database, vector, definition, key, or fallback
pointers.

No native definition generation field is proven. Object `+0x10` is a
process-local runtime ordinal. `definition_generation` is therefore a
resolver-owned, non-monotonic fingerprint of the loaded database topology and
selected identity under the proof epoch. It is only a short-lived lease token
for SCHEME6's double resolution. Unknown keys, build/RTTI/vtable drift,
fallback results, collisions without exact pointer agreement, duplicate
canonical keys, or lifecycle drift fail closed before a native submit.

## Acceptance boundary

The standalone test composes SCHEME5, SCHEME6, and this resolver for basic sway
and complex murder. It verifies exactly one submit, pending ACK, fresh
postcondition receipt, both internal resolver passes for each SCHEME6 pass,
and typed pre-submit RED for identity/lifecycle failures. Both `/Od` and `/O2`
builds use `/W4 /WX`. The evidence verifier is run under normal Python and
`python -O`; neither mode uses `assert` for acceptance.

Remaining work is shared build/bridge/schema/MCP wiring, heartbeat ownership,
and a fixed-version paused live validation. Those gaps are intentionally not
represented as GREEN by this private package.
