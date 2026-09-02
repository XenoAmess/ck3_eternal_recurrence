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

## Four-entry bounded live follow-up

An OFF-by-default candidate on parent baseline
`b078d3aa9cd77760fb627f9aff77b58d2eca4285` captured only the four entries
above. Common vectors were capped at 16 children, and the three CIf optional
pointers were read only at the statically proven `+0x258` offset. The capture
only compared vtables to `0x4461CA8`; it did not compute or evaluate duration.

The source contract passed `7/7`; the instrumented Release build and native
game-access test passed. Candidate identities were:

- `xar_ck3_bridge.dll` SHA-256
  `DD852843C961D73EA653D658A17751BEEEB84BCA37DFC4AC03BBFCB1EEDB95B7`;
- `xar_ck3_bridge_injector.exe` SHA-256
  `D5ED892C8B64F9DECED1726EB5A5B18A863D343C81FA4FE0CDED29C745117067`.

The live bound `open_kaishek`
`0390b9a959fa1a59a968000ed49e827a03b8d4e4`, the unchanged CLI JAR
SHA-256
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`,
and GREEN preflight artifact
`Z:\ck3_mod_rewrite_process_assets\zg361\open-kaishek-support-20260902T1836\g2-next-layer-corpus-preflight.json`,
SHA-256
`CD2509F1670B306FAC4BA6B0F1DA63B32E2DCFF47788D2B7F7C7EF1C35FFF220`.

The single live attempt retained:

- report
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-composite-ready-20260902T185429\live-openk0390\report.json`,
  SHA-256
  `A89D7EBE4BC31352D51BF0AB7FB1FE6351B288F71CF1B9482C00F478506DCDC3`;
- private JSONL beside it, SHA-256
  `DF77E246787B8B1EE11DCB933442FBECA66547C048F2E02674DE02B955FD011E`.

Both rows are identical and all four captures completed:

| Entry | Common capacity/count and child vtables | `+0x258` |
| --- | --- | --- |
| index 9 `CIfEffect` | not repeated; prior common child was `0x4446EF0` | null |
| index 10 child 3 scripted-list | `1/1`: `0x44D1D50` | not applicable |
| index 10 child 4 `CIfEffect` | `1/1`: `0x44D1E18` | null |
| index 10 child 5 `CIfEffect` | `2/2`: `0x44D2138`, `0x44D27B8` | null |

No common or optional entry matched `CAddTruceEffect<0>`. All three observed
`CIfEffect+0x258` fields are now conclusively null for this frozen loaded
tree; they must not remain listed as pending paths. Cleanup and source
invariants were GREEN, and no mutation or time advance was sent.

Index 9 is exhausted under the bounded RTTI-backed layout. The next static
entry is restricted to `0x44D1D50` and `0x44D27B8`: resolve their exact
COL/type/container semantics, then select only a uniquely justified nested
field. The recursive `0x44D1E18` occurrence remains a known CIf container but
does not by itself identify Truce. Public ABI/readiness and production shape
constants remain unchanged; `GEN-034` remains unresolved.

## Residual RTTI and frozen-source correction

The bounded offline extractor on parent baseline
`2ee8eab130477b9d346024d146337bf2213e78d0` resolved both residual vtables:

| Vtable RVA | COL / type descriptor | Exact RTTI | Size | Container semantics |
| --- | --- | --- | ---: | --- |
| `0x44D1D50` | `0x4B4FC98 / 0x5655F78` | `CShowAsTooltipEffect` | `0x60` | slot `0x3380980` walks the inherited `CJominiEffect` common vector at pointer `+0x40`, count `+0x4C`, dispatching child slot `+0x58` |
| `0x44D27B8` | `0x4B50238 / 0x5655EF8` | `CJominiContextEffect` | `0x100` | slot `0x3389790` walks common effect children at `+0x40/+0x4C`; `+0x60/+0x6C` is separate scope/configuration storage, confirmed by slot `0x3389610` |

Both are real containers, so RTTI alone does not choose between them. Frozen
stock-source order does: `raiktor_claim_cb.on_defeat` has exactly twelve
top-level effects, and index `7` is
`add_truce_attacker_defeat_effect`; indices `9/10/11` are respectively
`on_lost_aggression_war_discontent_loss`,
`laamp_as_mercenary_payout_tooltip_effect`, and
`mandala_war_defeat_effects`. Their definitions have respectively `4`, `1`,
`1`, and `2` top-level children, exactly matching the earlier live defaults
`7=4/4`, `9=1/1`, `10=1/1`, and `11=2/2`. Index `6` is the eight-argument
`modify_all_participants_fame_values` call and matches its live selector count
of eight. The descendant identities close the correlation independently:
index `9` reaches `CTargetingFactionsDiscontentEffect`, while index `10`
reaches the exact `CShowAsTooltipEffect -> Context -> active task contract`
shape authored by the LAAMP payout tooltip.

This corrects the prior shape-only narrowing: the unique truce scripted-effect
entry is index `7`, not either residual index `9/10` branch. The next private
read-only path is therefore only:

`root index7 default child1 (hidden_effect) -> child0 (scope:attacker Context) -> child0 (expected CAddTruceEffect<0>)`.

That path is source-correlated/static and still requires one bounded live
validation before any production contract can change.

The earlier `+0x258=null` result applies exactly to the three captured parent
`CIfEffect` objects. It does not prove that the distinct recursive CIf child
also has a null optional pointer. No further read of that child is needed for
the truce search because source correlation excludes the complete index `9/10`
branches; this is the precise closure, rather than propagating null across
objects.

Reproducible inputs and result:

- extractor: `extract_g2_truce_residual_rtti.py`;
- contract: `g2_truce_residual_rtti_v1_contract.json`;
- focused exact-build tests: `4/4` GREEN;
- artifact:
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-residual-rtti-20260902T1915\g2-truce-residual-rtti.json`,
  SHA-256
  `3A56A1ACBF49591C0787EADE412C2C8F23E49E253DAC00C4ADB7A7624B628DB3`.

No CK3 process was started. Public ABI, readiness, production shape constants,
and all mutation paths remain unchanged; `GEN-034` is still unresolved.

## Targeted index-7 live attempt: harness RED before capture

The OFF-by-default targeted reader was frozen on commit
`a3d2fb0f801840168ee64dfa27ab65ece5540c46`. Its only runtime path is
`index7 -> default child1 -> hidden_effect child0 -> Context child0`; it would
accept only the exact `CAddTruceEffect<0>` vtable and then expose the `+0x108`
input address without invoking the evaluator. Focused source/fixture tests were
`10/10` GREEN and the Release candidate DLL SHA-256 was
`C8B4D8015CE251FC09DD9AE4348BD469B57CF8F554349BB5B9698B17D8B6A036`.

The single authorized live attempt ended after `126.891s` with typed
`NativeReadinessTimeoutError` and `last=None`. Readiness, exact-build proof,
and the MCP sequence remained null, so execution never reached the private
reader. Consequently no private JSONL was created, the Truce vtable was not
observed, and `+0x108` was not frozen. This is a harness/native-readiness RED,
not a path-shape or capability RED, and it does not justify changing the
production `19/14/index9` constants or any public readiness field.

Evidence:

- report:
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-index7-targeted-ready-20260902T1930\live-authorized-index7\report.json`,
  SHA-256
  `6997DDA2C233974CE679F93C452A519E55CE309DAB8D3A4D50D6861A8BAE2C58`;
- cleanup summary beside it, SHA-256
  `6014C3EB76BFD48D6BDE3932E4343F20C827E2B59AF7EED1C0E4AA1AD6D91906`;
- checkpoint and driver source invariants were unchanged at
  `60108A5D...AF164` and `4FB901C7...FF57E`; cleanup was GREEN and CK3/probe
  inventory returned to zero.

No evaluator or mutation was called, game time did not advance, and no second
live attempt was started. `GEN-034` remains unresolved; the exact index-7 path
still needs one successful paused private capture in a separately authorized
run.

## Distinct readiness-300 package

The `122.731s` failed session is shorter than the `205.7s` same-checkpoint
GREEN control. That concrete control makes a `300s` readiness budget a distinct
load-window test rather than a repetition of the old `120s` timeout. The next
package freezes `--readiness-timeout 300` and a `420s` total session bound in
`g2_index7_targeted_readiness300_v1.json`; the exact index-7-only DLL remains
unchanged.

`prepare_g2_index7_targeted_readiness300.py` is a no-launch preflight. It
rejects a reused attempt directory, verifies the Python runtime, runner,
checkpoint, driver state, CK3 executable, DLL, injector, and open_kaishek
preflight hashes, checks the private v2 markers in the DLL, and emits one
PowerShell command. It cannot launch CK3. The verify-only artifact is:

`Z:\ck3_mod_rewrite_process_assets\zg361\g2-index7-readiness300-ready-20260902T2017\no-launch-preflight-v2.json`

with SHA-256
`3966520341699BCBA9BD7E4F2259068281E503A57CD08807BEC19FEA3E519DAA`;
the frozen manifest SHA-256 is
`A4A295A378AF943F0EB7FB82DB8C552395169F50ED8CB50E7510960671A733DB`.
All preflight/hash checks were GREEN and the future attempt directory remained
absent. Focused preflight plus private-reader source contracts were `10/10`
GREEN. This preparation started no CK3 process and does not authorize the live
command by itself.
