# Vivhite Courtier Standalone

## Product Contract

- Source root: `Eternal_Recurrence_Vivhite_Courtier/`
- Chinese title: 【琉焰卿的永恒轮回：典造琉焰廷臣·白绮特供版】
- English title: **Eternal Recurrence: Glassfire Courtier Creator - Vivhite Edition**
- Version: `1.0.1`; tested baseline: CK3 `1.19.0.6`
- Repository tag namespace: `vivhite-v<version>`; it must never reuse the original mod's `v1.0.0` tag.
- Workshop identity: item `3787304042`. The original item `3784706360` is forbidden in the standalone runtime and is not a default in its tooling.

The product contains only the paid custom-courtier creator. It has no recurrence, pact, game rule, shop, scoring,
contract, ledger, trait, event, on_action, tutorial lesson, or cross-save persistence dependency. Configuration is
save-local state on the current player character and persists only for close/reopen convenience.

## Isolation Contract

Every custom runtime definition and state key uses the `ervc` namespace: decisions, group, text icon, scripted
GUIs/effects/triggers/values, GUI type/name/state, character flags, variables/lists/scopes, localization keys and
loadable asset paths. The decision is available to any living human player and has both static and runtime AI gates;
it does not require the original `xa_enabled` pact flag.

The decision effect only sets `ervc_cc_open_pending`. A registered invisible GUI bridge consumes that flag, initializes
and rebuilds catalogs, then opens the modal. This preserves the proven workaround for CK3 decision-tooltip effect
previewing. Confirmation revalidates the full configuration and available gold, closes first, creates and delivers one
courtier, applies stats/traits/house, then charges exactly once. Failed delivery vanishes the temporary character and
does not charge.

The 27-file release allowlist has no shared VFS path with the original product except the launcher-required root names
`descriptor.mod` and `thumbnail.png`. Static validation also compares definition/localization/GUI inventories and
rejects any custom `xar`, `xa_`, `XAR:`, original Workshop ID, forbidden subsystem path, or original runtime dependency.

## Generation

`tools/gen_vivhite_courtier.py` reads only the independently pinned
`tools/vivhite_courtier_traits_1_19_0_6.json`. Ordinary generation never reads the ignored game installation. The
snapshot records CK3 `1.19.0.6`, source `00_traits.txt` SHA-256
`079f0ab5c4224c505ab9f25bca80d8df296e5899bfab26049ce5fe794dc0b042`, 301 source traits, 224 catalog traits and
95 conflict pairs. It emits three generated ERVC catalog files and supports `--check` parity.

`tools/compose_vivhite_key_art.py` renders the owner-supplied
`images/vivhite_courtier_key_art.png` to the standalone mod's 640×640 launcher/Workshop `thumbnail.png`. The static
validator reconstructs the RGB pixels exactly and still enforces PNG format, 640×640 dimensions and the launcher's 1 MB
limit. Encoded PNG bytes are not compared because zlib output is not stable across Pillow builds.

```powershell
py tools/gen_vivhite_courtier.py
py tools/gen_vivhite_courtier.py --check
py tools/compose_vivhite_key_art.py
```

## Localization Status

The standalone files own their `ervc` keys so the product loads without the original mod, but they do not fork the
already released translations. Of each language's 45 values, 43 must match the frozen original byte-for-byte after the
mechanical `xar` to `ervc` key/state namespace substitution. Only the decision title and decision-group title are
standalone branding deltas. The seven new edition/group values were translated with MiniMax-M3 assistance, then
manually normalized to each language's existing Eternal Recurrence, Glassfire and courtier terminology while preserving
`@ervc_decision_group_icon!` and `Vivhite`. The static validator enforces the 43-value inheritance contract, all 45-key
inventories, protected tokens, numeric literals, BOM and the absence of English group-title placeholders. Release review
therefore covers only the two branding deltas; it does not repeat the original mod's completed creator-window language
sign-off.

## Build And Static Gates

```powershell
py tools/test_build_vivhite_release.py
py tools/validate_vivhite_static.py
py tools/build_vivhite_release.py --check
py tools/build_vivhite_release.py
```

The builder copies an exact 27-file allowlist and emits deterministic staging, manifest and ZIP. Normal/check/tag
artifacts record `workshop_item_id: null`; the new ID remains only in the user-directory outer `.mod`, as required by
the product contract. A formal release requires a clean `vivhite-v<version>` tag. For post-upload verification only,
build an otherwise identical local manifest with `--workshop-item-id <digits>` and do not publish or commit that
sidecar. Downloaded-cache verification uses the same strict PDX descriptor normalization as the original release and
requires this temporary manifest's non-null ID.

Current pinned-environment L0 is GREEN: 4 succession projection tests, 6 original release tests, 17 Vivhite release
tests, both static validators, scoring reference vectors and both deterministic double builds. Untagged candidates
intentionally record both `git_tag: null` and `workshop_item_id: null`. A formal build replaces only the null Git tag
after proving the canonical source, clean worktree and matching `vivhite-v<version>` tag; the original Workshop item
remains rejected.

## 1.0.1 Update Scope

Version 1.0.1 replaces only the standalone launcher/Workshop thumbnail with dedicated Vivhite courtier key art. It also
adds the existing decision illustration as the first Workshop-description image and embeds the eight accepted real-engine
creator screenshots in their documented order. Script, GUI, localization and gameplay bytes are unchanged. The release
still requires a clean committed three-cell acceptance run, `vivhite-v1.0.1`, a deterministic 27-file artifact, upload to
the existing item `3787304042`, and fresh downloaded-cache verification.

## Runtime Acceptance

`tools/run_vivhite_acceptance.py` runs three serialized, non-debug CK3 cells. A formal run uses the default `all`
selection and omits `--keep-userdirs`; individual scenarios are available for diagnosis:

```powershell
& "tools\.venv\Scripts\python.exe" "tools\run_vivhite_acceptance.py"
& "tools\.venv\Scripts\python.exe" "tools\run_vivhite_acceptance.py" --scenario vivhite-alone
& "tools\.venv\Scripts\python.exe" "tools\run_vivhite_acceptance.py" --scenario original-then-vivhite
& "tools\.venv\Scripts\python.exe" "tools\run_vivhite_acceptance.py" --scenario vivhite-then-original
```

1. Vivhite alone proves open/cancel, 119-gold disabled confirm, default 120-gold purchase, configured 348-gold purchase, selected Aluk faith context, close/reopen retention and AI rejection.
2. Original then Vivhite proves both independent decision groups and modals render; ERVC keeps its 348-gold state while XAR keeps its 120-gold state, and each product delivers exactly one courtier with one charge.
3. Vivhite then original repeats the dual assertions to detect VFS or definition replacement caused by load order.
4. Every cell requires each ordered fixture marker exactly once and zero blocking project-attributed duplicate-definition, GUI parser, localization, missing-variable, `xa_`, `xar`, `ervc` or `erva` diagnostics. The only narrow exception is the frozen original release's two loc-only `xa_curse_a_rarity` / `xa_curse_b_rarity` unused-variable warnings; each occurrence is retained in `allowed_project_diagnostics`.

Each cell builds fresh production projections for the selected products and adds the external 12-file `erva` fixture
last. The standalone projection strips every `# ERVA_DUAL_ONLY_BEGIN/END` region, so it never references the absent
original product. The runner creates a new disposable `-userdir`, disables cloud saves, writes outer descriptors with no
Workshop identity, and constrains every runtime path to that directory. It never synchronizes or loads a real Workshop
cache.

Preflight and postflight compare the real CK3 profile, local Steam cloud backing store, every registered CK3 UGC
descriptor and recursive metadata for each registered Workshop target. The baseline must remain stable for five seconds
after CK3 exits. A GREEN formal cell also removes its disposable userdir; `report.json` and JUnit `report.xml` record the
runtime hashes, load order, fixture ordering, marker evidence, diagnostics and protected-storage hashes. GitHub's
official runner has no CK3 or interactive desktop and must run only the static fixture/runner contracts.

### 1.0.0 Release Evidence

The clean committed-candidate schema-v2 non-debug matrix `ervc_release_clean_6575997_20260821` completed all three
cells GREEN on CK3 `1.19.0.6` in 910.962 seconds. Its report binds full Git SHA
`6575997b14a90b0afda75fdde304170206478c21`, JUnit records 3 tests and 0 failures, and every cell has an empty blocking
`project_diagnostics` list, an unchanged runtime tree and `userdir_removed_after_run: true`. Both dual cells explicitly
record four cold-boot occurrences of the two frozen original-release warnings above. The shared disposable-userdir
parent and all three detached watchdog processes were absent after the matrix.

- Vivhite production projection: `6242ca7eec1b33f6da939c3a161b7338011122780c4740c6e831e2de0e20577c`.
- Original production projection in both dual cells: `97b9f386ab17364eec0859be1f7c6407816a27a396b2edcf6427d697789ba2ab`.
- Standalone fixture projection: `dd049976adfec06a4dccb8244f33709582d37474d0249a49ecac57d6ec268359`.
- Dual fixture projection in both load orders: `8d5a9da92445a97bf80b2037b95fd717b88c9b5eaa4c61cd74695d510d82ba75`.
- CK3 executable before/after every cell: `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`.
- Protected-storage aggregate before/after: `ed9a9cce6db99148f08aac997d38caae00f64c79827fdb1dcf642c3af9c38336`.

The bounded protection set contained nine real-profile files, two local Steam cloud files, 82 registered Workshop
targets and 162,960 target metadata entries. CK3's debug mount records exactly matched each requested product order and
the fixture was last. The final snapshot started only after a complete baseline-equivalence scan, waited five seconds,
then completed another full scan.

Tag `vivhite-v1.0.0` points to that exact commit. Its 27-file formal manifest SHA-256 is
`643164d9b0537802fa13f5b88029ab8a34aa12496f8ac1579f3436beb8fa9d66`; its deterministic ZIP SHA-256 is
`68154ad507b654eb31cf08e51dfc45ae8bb9a576c54e94b137953b8fb9175c2e`. Local output, official Windows tag workflow
artifact and [public GitHub Release](https://github.com/XenoAmess/ck3_eternal_recurrence/releases/tag/vivhite-v1.0.0)
digests match. Official master run `32457377134` and tag run `32458755796` are GREEN. New Workshop item `3787304042`
was forced into an initially absent cache path and passed strict `--workshop-cache` verification for all 27 files. The
anonymous Steam API reports public visibility, and the initial 1.0.0 public page exposed exactly eight accepted screenshots. These
results close the clean-candidate, fresh-cache and external-delivery gates for 1.0.0.
