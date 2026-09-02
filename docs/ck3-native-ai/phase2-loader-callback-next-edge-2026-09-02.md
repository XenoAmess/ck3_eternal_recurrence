# Phase-two loader callback next-node edge (2026-09-02)

This offline package closes one new exact-build observation point after the
bounded callback-sequence NO-GO. It inspects only the already identified loader
loop `[0x3B9AB00, 0x3B9ACED)`. CK3 was not started, and no production loader,
public bridge, or readiness state changed.

## Provenance

The clean branch started from parent baseline
`4e0927c64ff5d72958bea87f4a1e47cdb11ad89a`. The executable remains CK3
`1.19.0.6`, size `95,206,008`, SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

The immediately preceding offline preflight was reused because the executable,
`open_kaishek` commit, and CLI JAR are unchanged:

- `open_kaishek`: `17caa288eb980aab0b652358e9e94a9901131619`;
- CLI JAR SHA-256:
  `421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`;
- artifact:
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\later-stalled-open-kaishek-preflight.json`;
- artifact SHA-256:
  `1E8DCBC7EBAB3D1D23EF31DF5684AAF61B81FAE8BC0BDE92A1C57E8F2F770F30`.

The reproducible extractor is
`ck3_autonomous_player/native_bridge/research/extract_phase2_loader_callback_next_edge.py`.
Its output is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\callback-next-edge-static-extract.json`,
SHA-256
`20454FC337ADB25AEFCE8BA80FB07305EA8C9F844251D9C429F795B55940E6DA`.

## Exact next-node edge

At function entry the owner supplies a pointer-vector range:

1. `RBX=[owner+0x70]` is the begin iterator;
2. the signed count is loaded from `owner+0x7C`;
3. `RDI=RBX+count*8` is the end iterator.

After callback return at `0x3B9AB93`, the exact 305-byte post-callback window
ends at `0x3B9ACC4` and has SHA-256
`D624CA70C1CAE6E3178AAB95D6369CFF96FD9CED8CD87B6BBEB2EB1CBA2B234D`.
Its final iterator edge is unique:

| RVA | Exact operation |
| --- | --- |
| `0x3B9ACB7` | `RBX=RBX+8` |
| `0x3B9ACBB` | compare `RBX` with end iterator `RDI` |
| `0x3B9ACBE` | if unequal, branch to `0x3B9AB50` |
| `0x3B9AB50` | load `RSI=[RBX]`, the next current node |
| `0x3B9ACC4` | exhausted-vector fallthrough |

The 13-byte edge has SHA-256
`03F8709D2D31472468E72873F81E2635305BCB5CFB81004B7DE721BFDC7BC8E8`.

## Closed stop point and wait boundary

The new primary stop point is **RVA `0x3B9AB53`**. The preceding instruction
has already loaded `RSI=[RBX]`, while the `node+0x88` callback-null gate has
not run. At this point a private observer can read:

- current node from `RSI`;
- node name pointer from `[RSI+0x08]`;
- callback receiver from `[RSI+0x88]`.

Every nonempty iteration reaches this point. It therefore covers exactly the
gap in the previous callback-only capture: a node with null `node+0x88` never
reaches callback call RVA `0x3B9AB90`, but it does reach `0x3B9AB53`.
RVA `0x3B9ACC4` is the supporting discriminator for an exhausted or initially
empty vector.

There is no uniquely attributable wait edge inside this bounded function.
Calls at `0x3B9AC2C`, `0x3B9AC45`, `0x3B9AC6E`, and `0x3B9ACB2` remain opaque;
source symbols or runtime evidence would be required before assigning wait
semantics to any of them. This does not invalidate the node-loaded stop point,
but it prevents claiming that the static slice found the later stall itself.

Phase two remains **native-readiness RED + not-live**. The next step is only a
proposal pending separate authorization: one bounded private exact-build run
using `0x3B9AB53`, the existing callback entry/return points, and `0x3B9ACC4`.
Success means recording the first node loaded after the last returned callback,
including its name and callback receiver, or proving that the vector exhausted.
Repeating a callback-only timeout would not add evidence.
