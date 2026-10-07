# Grant title picker and ordinary interaction: actual 1.20.0.4 source binding

The C3 path requires granting a new independent title to current same-faith NPC
65865. This source change supplies the missing actual 1.20.0.4 Grant picker and
ordinary interaction dependencies. It has no native build or runtime acceptance;
the fresh C3 title grant, holder result and business credit remain pending.

The admitted actual image is CK3 1.20.0.4, Steam build 25734779, 101040248 bytes,
SHA-256 `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The identity is inherited from the owner's frozen
`ck3-local-update-20261007-001/FINAL-001/UPDATE-AND-GIT.actual.json` receipt.
The old exact 1.20.0.3 image, binder and pin includes remain separately admitted.
An actual .4 image cannot use the .3 native binder or GUI profile.

| Native operation | Exact .3 RVA | Actual .4 RVA |
| --- | --- | --- |
| GetTitles | `10E5CD0` | `10E5CD0` |
| Row title / selected / selectable / toggle | `10EC1F0` / `10EC2F0` / `10EC4B0` / `10EC0E0` | same individual entries |
| Grant can-send / send | `117C530` / `117BAE0` | `117C520` / `117BAD0` |
| Copy confirmation context | `10E6FF0` | `10E6FE0` |
| Handler open enum 15 | `AF34A0` | `AF34A0` |
| Grant first open | `117EFF0` | `117EFE0` |
| Confirmation refresh / updater | `10E7810` / `10E7A90` | `10E7800` / `10E7A80` |
| Shared IsOpen | `21603A0` | `2160380` |
| Ordinary shown / option / intermediary answer | `30796B0` / `3078880` / `307C360` | `3079690` / `3078860` / `307C340` |
| Send command constructor | `2968170` | `2968150` |

These are individual mappings. The actual Grant mappings include unchanged,
minus-0x10 and minus-0x20 entries. Original and minus-0x20 candidates that did not
identify the target function were preserved as rejected candidates; no common
image delta admits a method.

Actual .4 primary Grant and Confirmation vtables are `452DBE8` and `45250E8`,
with type descriptors `5742F58` and `5731D88`. Both primary slot `+38` entries
resolve to `2160380`. Actual title primary vtable is `4712A28`; the old address
now identifies a secondary component with COL offset 8 and is rejected. Send
command primary/secondary vtables are `448BCF0` / `448BCC0`. The finite packets
verify COL signature, object offset, self RVA and exact mangled class names.
Logical/Gfx/Handler types reuse the sibling private GUI packet, with primary
vtables `44D6058` / `44BC418` / `44BA8A0` and type descriptors `55072C0` /
`5514460` / `5694B20`.

Confirmation refresh is an actual source change, not a byte-equivalent shifted
function. The .4 refresh calls `10E7A80` unconditionally. That updater clears
confirmation `+11DC`, then checks definition `+26FA == 1` before producing its
type-1 rows. The kind-2 Grant path uses the real .4 stock functions. Both complete
bodies are included in the .4 pin projection, including the relocated guard.

`BindOrdinaryInteractionImage12004` reuses the canonical actual .4 Core,
InteractionContext and Command binders plus the sealed actual Send constructor
and vtable constants. It supplies the separately captured shown, option and
intermediary-answer entries. The owner wrapper checks 20 actual .4 code prefixes;
the Grant wrapper checks 13 complete native bodies plus those ordinary prefixes.
The .3 pin includes remain untouched.

The provider still requires full-generation recipient/title identities, exact
paused owner/current frame, typed stock models and back pointers, two stable
complete row reads, exact expected selection, actor-owned selectable title rows,
native can-send, and the stock warning guard. A sent result only verifies transfer
after resolving the current model afresh and rereading every selected full title
holder as the requested recipient. `business_full_credit` remains false. C3
same-faith eligibility and protected-title policy retain their existing consumer
contracts.

The wire schema `ck3_12003_grant_title_picker_v1` remains the shared V1 software
schema. The result now reports its actual `exact_build` and `executable_sha256`.
Ordinary wire source/build metadata similarly records the selected actual image.
Bridge admission can use `IsGrantTitlePickerBuildV1(descriptor)` and must select
the matching actual GUI environment; the .4 provider requires `crozier12004`.

Evidence is preserved under
`C:/workspace/ck3_lyd_runtime_20261004/r20-native-adapter-review-sourceonly-20261007-001/grant/`:

- `FINITE-GRANT-CAPTURE-001.FAILURE.actual.json` and `002.FAILURE.actual.json`
  preserve the leaf `.pdata` and rejected minus-0x20 discovery failures.
- `FINITE-GRANT-CAPTURE-003.actual.json`: finite native bodies, RTTI types and
  original/minus-0x20 candidates; 23050 bytes read.
- `FINITE-GRANT-CAPTURE-004.actual.json`: five missing Grant entry closures;
  9134 bytes read using bounded `.pdata` entry lookup.
- `FINITE-GRANT-CAPTURE-005.actual.json`: complete old/new updater; 1649 bytes.
- `FINITE-GRANT-CAPTURE-006.actual.json`: option dependency and title primary
  type; 1516 bytes.
- `PROJECT-ACTUAL4-PINS-001.actual.json`: 640 additional bytes for 20 exact
  prefixes, complete body sizes/SHA-256, input receipt hashes and projections.

No whole-image reads, process inspection, game calls, SDK calls or native builds
were performed in this lane. The exact-file read evidence is source evidence,
and all packets record `whole_status: NOT_GREEN` and `future_pass: null`.

Five pure Python source/projection checks passed under optimization:

```text
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe -O ck3_autonomous_player/native_bridge/tests/test_grant_title_picker_12004_source.py --capture-root C:/workspace/ck3_lyd_runtime_20261004/r20-native-adapter-review-sourceonly-20261007-001/grant -v
```

The same source test can run without `--capture-root` in a clone; the optional
receipt binds the exact generated body hashes. `unittest` failure checks remain
active under `-O`. Native compilation/linking and the real C3 grant remain owner
gates. Existing ordinary native test targets require the complete actual .4
runtime link closure because the new binder reuses canonical provider functions.
