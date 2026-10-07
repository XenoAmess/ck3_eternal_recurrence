# Existing private decision and normal exit paths on CK3 1.20.0.4

2026-10-07 / LYD R20 source successor. **SOURCE_ONLY; native qualification
AUTHORED_NOTRUN; whole goal NOT_GREEN; future PASS null.** This packet ports the
existing private decision opener, keyed model reader/select/confirm path and
normal map exit provider. Their existing flags and caller policy remain the
Root's responsibility. The earlier generic GUI migration explicitly left the
private flags OFF and did not qualify this LYD ON selection.

The target is the actual installed Crozier 1.20.0.4 / Steam 25734779 / EXE
101040248 bytes / SHA
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
Identity is reused from
`C:/workspace/ck3_lyd_runtime_20261004/ck3-local-update-20261007-001/FINAL-001/UPDATE-AND-GIT.actual.json`.
The old frozen executable remains under `installed-before-update/ck3.exe`.
No new EXE hash, whole image read, process attachment, native build, SDK call,
game launch, screen input or save-body access was performed here.

The independent actual .4 GUI environment and complete named common GUI spans
come from [the generic GUI source topic](generic-gui-default-path-migration-12004.md):
FindTop `3AAB0E0`, Shortcut `3ABC4B0`, strict descendant `3A78210`, and ButtonBase
slot 13 `3AA0D20`. The four original loaded-image 32-byte guards select those
current locators through the existing GUI profile helpers. The strict shared
identity predicate requires the matching version, SHA and GUI revision; .4
cannot select the retained .3 coordinates.

The private finite packet is
`C:/workspace/ck3_lyd_runtime_20261004/r20-native-adapter-review-sourceonly-20261007-001/private-gui/`.
`FINITE-PRIVATE-GUI-CAPTURE-001.actual.json` preserves every named candidate,
raw span and section mapping. It used the existing checked-in
`research/disasm_ck3_bounded_disk.py` bounded reader, imported without invoking
its old CLI. New source capture was **3,502 bytes / 60 finite reads**, plus
**two 4,096-byte bounded PE header reads**. No section scan, executable-wide
search or raw pdata traversal was used. The frozen section metadata was shared
with the independent Grant lane to avoid another PE parse.

| Named actual .4 primary role | Vtable | COL | Type descriptor |
| --- | --- | --- | --- |
| `CInterfaceApplication` | `449BDB8` | `4A27528` | `5667F58` |
| `CInGameInterfaceIdler` | `44D6058` | `4A84D78` | `55072C0` |
| `CIngameInterfaceIdlerGfx` | `44BC418` | `4A5B340` | `5514460` |
| `CIngameInterfaceHandler` | `44BA8A0` | `4A59370` | `5694B20` |
| `CDecisionsView` | `455CC90` | `4B62A80` | `5794D80` |
| `CDecisionDetailView` | `455D4F8` | `4B62F88` | `5795050` |
| `CDecisionType` | `48BD150` | `4F7D500` | `5586B90` |
| `TPdxNullObject<CDecisionType>` | `48931A0` | `4F16E78` | `5AB0518` |

Each table is adopted from its own primary COL, self RVA, type RVA and exact
mangled class name. The old table and old-plus-`10` were only finite named-role
candidates. Every old candidate was rejected. The old DecisionType coordinate
now names `SDecisionAdvice`, which is why a universal table shift or merely
changing SHA/version is insufficient.

| Original consumed code role | Actual .4 RVA | Source span and boundary |
| --- | --- | --- |
| Group-vector getter | `1456090` | Complete 8-byte getter, offset `258` |
| Decision-definition getter | `A935B0` | Complete 4-byte getter, row offset `0` |
| Original row `OnSelect` | `14582B0` | Complete 189 bytes |
| Row selection wrapper | `1459510` | Complete 28 bytes, unchanged RCX forwarded to OnSelect |
| Original `SetDecision` | `1471630` | Complete 205 bytes |
| Detail dispatcher prefix | `1471210` | Actual SetDecision tail target; original 32-byte guard preserved |

`CAPTURED-FUNCTION-CLOSURE-001.actual.json` records complete nonrelative
operands, member offsets, local branch structure and ordered actual relative/RIP
targets for the complete spans. `SetDecision` still binds current-player
reference `54DBC00` and character storage `5C67568`. Its tail target identifies
the detail dispatcher. That dispatcher's original 32-byte prefix matches exactly;
it ends within an instruction and is credited only as the existing byte guard,
not as a complete method. The actual .4 pin include freezes complete OnSelect,
wrapper and SetDecision bytes and that unchanged prefix.

The keyed reader keeps all original logical/Gfx/Application backlinks, stamped
Jomini owner equality, list/detail handler/root bindings, bounded group and row
vectors, row owner equality, stable double census, native definition key rules
and empty-selection null-object identity. Failure diagnostics continue to
describe the first failed original guard and never admit an object. Original
select/confirm/outcome parsing, typed predispatch refusal, actor identity,
no-visible-modal checks, fresh Snapshot equality, receiver census, separate
postcondition reads and consumed-fault/no-retry semantics are preserved. The
Aub-specific business path remains .3 because it is outside the LYD request.

The normal exit provider keeps its default OFF flag, exact process creation
identity, retained owner ticket/TLS, source inventory verification, fresh native
census and signed query binding. Every original `Process`, `Owner`, `Frame`,
`Inspect`, `ReadCensus`, `Same`, `Current`, `Signature`, `BoundQuery` and
`DispatchStage` body is byte-identical in source. The continuation and lifetime
CAS tail are unchanged. A consumed dispatch remains unknown until its original
independent readback; reconnect and revision changes do not clear a claim.

Opener and keyed-result serializers use the admitted descriptor's version/SHA
and retain the original .3 defaults for old callers. Existing schemas, keys,
counts and gameplay meaning are unchanged. Native boolean/ACK does not prove
visibility, the selected decision, its event/effect, orderly process exit or
autosave success.

`SOURCE-FOCUSED-CHECK-001.actual.json` passed 41 finite ABI/source checks,
including current pin bytes, historical source bytes, each named table, original
model/action guard preservation, exit claim/continuation preservation and
descriptor-backed wire identity. This is source-level evidence only. The
`open_kaishek` precheck is not applicable: native RTTI/image bytes and C++ owner
guards are outside its script parser/validator/finite runtime semantics.

`ingame_private_gui_12004_profile_v1_test.cpp` is an authored offline native
identity/profile fixture. It checks actual and historical exact tuples plus
cross-build SHA/version/revision and legacy-profile refusals. Root must add its
CMake target, compile and run it; it has not run here and supplies no positive
native model, GUI action, process-exit or real CK3 qualification. Root owns the
bridge worker hooks, Python exact identity consumers, CMake, the single build/SDK
entrance and the subsequent actual .4 native/live evidence.
