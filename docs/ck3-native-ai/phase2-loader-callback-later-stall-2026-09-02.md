# Phase-two later loader callback boundary (2026-09-02)

This package performed the one authorized, bounded private callback-sequence
observation. It did not modify the production loader or public bridge. The run
closed **NO-GO** because the 60-second boundary did not expose either a callback
that failed to return or a next node waiting to enter the callback.

## Preflight and exact-build boundary

The required offline preflight used `open_kaishek`
`17caa288eb980aab0b652358e9e94a9901131619` and CLI JAR SHA-256
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
Its artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\later-stalled-open-kaishek-preflight.json`,
SHA-256
`1E8DCBC7EBAB3D1D23EF31DF5684AAF61B81FAE8BC0BDE92A1C57E8F2F770F30`.
Parser/IR/runtime remained GREEN; the full-root schema-only validator retained
its known RED. This preflight is structural evidence, not CK3 live evidence.

The private probe executable had SHA-256
`7B33E76BD6E6907BFB91B9AD7015AD214437BFCE83F5519103C52A464CC60D16`.
The only live run was bound to CK3 `1.19.0.6`, executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`,
and an isolated user directory. It lasted 60.264 seconds against a 60,000 ms
limit.

## Observed entry/return sequence

The live artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\later-stalled-callback-sequence.json`,
SHA-256
`7E1B3A97558F1BCF5F1B507022988BE55515C9BDCB0A024E9317C8AB0A8F9976`.
It recorded two complete same-thread entry/return pairs:

| Sequence | Node | Concrete callback | Global pointer | Global vptr | Global slot 2 | Result |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `CGameConceptTypeDatabase` | `0x2045330` | `0x570C0F0` | `0x4403F88` | `0x2C4CCA0` | returned |
| 2 | `CJominiLoadScreenDatabase` | `0x3455CA0` | `0x57D7B50` | `0x44E4728` | `0x3453430` | returned |

Both used the already bound wrapper vptr `0x408A450` and wrapper slot-2 target
`0x947BD0`. Sequence 1 entered at 13.185 seconds and returned at 13.296;
sequence 2 entered and returned at 14.717 seconds. The last successful sequence
is therefore 2. There is no first unreturned sequence.

At the 60-second boundary the last callback thread was suspended outside
`ck3.exe` at absolute instruction pointer `0x7FFE27F35312`. Its callback-node
register was zero, so the probe could not assign a node name, receiver, global
vptr, slot 2, or concrete target to the wait. The numeric subtraction emitted
in the raw artifact as `timeout_thread_rva` is not a valid CK3 RVA and must not
be used as one.

## NO-GO and next entry

This result rules out the two observed callbacks as the later stalled callback,
but it does not distinguish a caller-side wait after sequence 2 from a later
node that never reaches callback entry. Phase two remains
**native-readiness RED + not-live**. No public query, production detour, or
readiness claim follows.

The next bounded entry is static: slice only the callback caller around RVA
`0x3B9AB90` after the successful return and bind its next-node advancement and
wait edge. A further live observation is authorized only after that work yields
a concrete caller-side stop point. Repeating this 60-second sequence capture,
the old 300-second timeout, or a whole-executable scan would not add evidence.

Cleanup was GREEN: both breakpoint bytes were restored, the isolated CK3
process was terminated, the real profile was not targeted, and no CK3 or probe
process remained after the run.
