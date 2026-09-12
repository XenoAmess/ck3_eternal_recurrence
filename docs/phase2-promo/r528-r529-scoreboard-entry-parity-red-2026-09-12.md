# R528/R529 scoreboard entry parity RED (2026-09-12)

## Verdict

R529 produced the retained state that R527 lacked. The accepted native `open`
action reached a stable received scoreboard surface: modal, panel, received HUD
entry, received tab, received page, backdrop close and header close were all
effective-visible. Managed/system entries and pages were hidden. The received
list ACL was also decoded and available.

That state is consistent with the product GUI but contradicted the native
canonicalizer's assumption that an open modal must hide all three HUD entries.
`zg361_scoreboard_toggle` and its three entries are siblings of the modal, and
their `visible` expressions do not depend on `zg361_scoreboard_open`; the modal
overlays the matching entry instead of hiding it. The provider therefore
returned `unavailable/state_projection_unavailable` for a real valid UI state.

P1 remains `9/9 GREEN`. P2 remains `0/8`: the failed 6.68 MB take contains no
qualified clean span, so editing, export and publication do not advance.

## Rounds and cleanup

- R528/PID `178116` ran the isolated Frontend warm-up with bridge injection
  disabled. It reached an authenticated responsive Frontend and was terminated
  with `tree_gone=true`, job count zero and empty global inventory.
- R529/PID `60960` was then the sole gameplay instance. It used CK3 `1.19.0.6`,
  the isolated userdir, `-loadsave=autosave`, bridge
  `F4EE46CF3426FCE26FABE1D4BD2A09C76AC0A813DEA7E62517383EDAB61CEB9F`
  and injector
  `0CC7554DA62FD4E6BEE03A38C28AFBCDFC81CF3D960C54AB7FCBF8CB90A08597`.
- The loader, feature manifest, paused seed, HUD and closed-state provider gates
  passed. The action was accepted; the later query retained the precise surface
  state above and then remained RED.
- Cleanup is GREEN. R528 and R529 are terminated; CK3, FFmpeg and injector
  inventory is empty.

## Minimal correction

The provider still requires exactly one visible entry in every stable state.
When closed, all pages must remain hidden. When open, exactly one page must be
visible and its managed/received/system surface must match the single visible
entry. Zero entries, multiple entries, multiple pages or a mismatched entry/page
remain `state_projection_unavailable`.

The semantic canonical byte position is unchanged, but its research name is
corrected from `visible_closed_entry_u8` to `visible_entry_u8`. No response
field, type, enum, tool, capability, ACL, action, allowlist, readiness rule or
version changes. The native fixture now models the actual product open state by
keeping the received HUD entry visible beside the received page.

Focused validation only:

- native scoreboard state executable: exit `0`, SHA-256
  `3E08BFADC08C87CA09DB22923835F8650C631E131305ABB33B6A9F4936A76FB8`;
- Python scoreboard state/action contracts: `17 passed, 22 subtests passed` in
  `0.76s`;
- `git diff --check`: GREEN.

The internal canonical data-semantics correction triggers a documentation-only
open_kaishek compatibility sync after the root commit. A fresh DLL is required
before one bounded R530/R531 verification; the R529 DLL must not be retried.

## Evidence

- no-launch plan: `BBF7BEEF5B982016DF43B67DEA515197180A8EF753920DFD1BAE2A2E1237F131`
- outer report: `09AB24607FE39277879B28E54002979D5970F0B246DF8EC309597120E23D27E9`
- inner report: `5F4E43BC623811FB90CD39E996A1BDCBCDC90AA75B6A547EA5190B0F0798DA1C`
- visual action cell: `06E731457EC396C5CD441C89BE77644797658C4352BF58F9782D457BFBA2C14C`
- cleanup: `65C4D4BACD94EBF6765FBEBE1660D1A14F221F1574CE71BE6A184C8512B911EF`
- timeline: `3F5ECEC7EF42C0C57E9CAD412FF21F750131C19BDA446AE867B3F8C443DD61C2`
- evidence index: `90CEFD7FB50EA0642453D94C78B5C2D2DB74AC76A6A1CEE3CC0196408AF63B5F`
- failed MKV: `3887EC304F8740BA85C3DCBED98A55BF2FF43712A6F673195B11E52BA61094E5`
