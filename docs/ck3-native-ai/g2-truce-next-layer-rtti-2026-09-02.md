# G2 truce next-layer RTTI classification (2026-09-02)

This is a read-only exact-build follow-up to the bounded `1 + 6` child
enumeration. It resolves the five unique observed vtable RVAs through MSVC
x64 RTTI and classifies only the container shapes justified by the class
hierarchies and deleting destructors. It did not start CK3 or change any
public bridge, readiness, production tree constant, or action path.

## Frozen input and reproducible extractor

- Parent baseline: `6a393bee99f07f8bed69b72e03cba59a4688c9c1`.
- CK3 `1.19.0.6` executable SHA-256:
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
- Extractor:
  `ck3_autonomous_player/native_bridge/research/extract_g2_truce_next_layer_rtti.py`.
- Contract:
  `ck3_autonomous_player/native_bridge/research/fixtures/g2_truce_next_layer_rtti_v1_contract.json`.
- Extracted artifact:
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-next-layer-rtti-20260902T184647\g2-truce-next-layer-rtti.json`,
  SHA-256
  `ABCDF8D0D4C595CF42187E0C7CAE4B8E5820A482A586B87D04BCF6C56AAA0117`.

The focused exact-EXE test passed `4/4`. For each entry it verifies the vtable
`-8` CompleteObjectLocator pointer, self-relative x64 COL, primary object
offset, type descriptor, full base hierarchy, first twelve slots, scalar
deleting destructor, and encoded object size.

## Exact RTTI identities

| Vtable RVA | COL / type descriptor RVA | Exact RTTI type | Size | MultipleTarget base |
| --- | --- | --- | ---: | --- |
| `0x4446EF0` | `0x4AB0FC0 / 0x55D1758` | `CTargetingFactionsDiscontentEffect` | `0x168` | no |
| `0x44D2138` | `0x4B4FD60 / 0x5656100` | `CSaveEventTargetAsEffect<1>` | `0x68` | no |
| `0x44786C8` | `0x4ACE7D0 / 0x55DFE68` | `CSaveScopeValueAsEffect<1>` | `0x278` | no |
| `0x41B1E90` | `0x479C520 / 0x5320BB0` | `CScriptedListEffect<CEveryInScriptedListEffect, CCharacterActiveTaskContractList>` | `0x270` | yes |
| `0x44D1E18` | `0x4B50288 / 0x56570B8` | `CIfEffect` | `0x260` | yes |

The frozen target `0x4461CA8` independently resolves to
`CAddTruceEffect<0>` (COL `0x4AC06B8`, type descriptor `0x55D9598`, size
`0x1F8`). None of the five observed identities is an alias for the target.

## Bounded container result

The hierarchy proves only `0x41B1E90` and `0x44D1E18` derive from
`CMultipleTargetEffect`. Therefore the common multiple-target walk can exclude
the index 9 child `CTargetingFactionsDiscontentEffect`, index 10 children 0/1
`CSaveEventTargetAsEffect<1>`, and index 10 child 2
`CSaveScopeValueAsEffect<1>`.

The `CIfEffect` deleting destructor adds one stronger layout fact. At RVA
`0x338C2DF` it loads `this+0x258`, skips when null, otherwise calls the
pointee's vtable slot 0 with delete flag 1. Thus each observed `CIfEffect` has
an optional owned effect pointer outside the already sampled common vector;
the previous `1/1` child capture cannot exclude that branch.

Four bounded positions can still lead to a nested effect:

1. index 9's already observed `CIfEffect`: inspect only `+0x258`;
2. index 10 child 3, the active-task-contract scripted-list effect: inspect
   only its common effect vector;
3. index 10 children 4 and 5, both `CIfEffect`: inspect their common effect
   vectors and `+0x258` optional pointers.

Static RTTI does not distinguish which of those four positions owns
`CAddTruceEffect<0>`, so this package deliberately does not promote a unique
path. The next read-only entry must be bounded to those fields; it must not
revisit the four excluded leaf positions or any earlier root/Context prefix.
Until that evidence exists, `evaluated_days`, expiry, decision, and action
remain not-live, the production `19/14/index 9` constants remain unchanged,
and `GEN-034` remains unresolved.
