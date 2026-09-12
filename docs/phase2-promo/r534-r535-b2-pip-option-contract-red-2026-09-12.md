# R534/R535 B2 PIP option-contract RED (2026-09-12)

## Verdict

R535 proves that the R533 cleanup correction works: the run opened, recorded and
closed the real scoreboard span, drained the surface, then entered the second
`phase2_receipt_appeal_pip` choreography. The exact product event `zg361b2.40`
appeared on the played character with three shown and enabled options. The B2
action cell stopped before input with
`ValueError: PIP option 1 semantic text changed`.

The product and its generator contain the expanded 365-day-plan descriptions,
while `tools/zg361_phase2_b2_action_cell.py` still allowed only older shortened
labels. The event identity, saved owner/subject scopes, option count/order and
availability all passed. This is a real current-product/acceptance-contract
mismatch, not a gameplay effect failure or a native event-observation failure.

P1 remains `9/9 GREEN`. The first clean span still belongs to an incomplete RED
take and is not promoted independently; P2 remains `0/8` until one complete
intake-ready capture closes all eight spans.

## Rounds and evidence

- R534/PID `195356` completed the isolated Frontend warm-up and terminated
  before gameplay.
- R535/PID `197116` was the sole gameplay instance on CK3 `1.19.0.6`, using
  `-loadsave=autosave`, root
  `c2371b25f0c84544cce942f0c447765bf4a2b34e`, bridge
  `3D41E88ABB0FD5CF812D67CB233D2BFD7A01A7661358E7D9375BCFD31E23CF48`
  and injector
  `6A4E7A045F54771BB027AC8E0B89B6BE131A62D99BCE239CC28BA0A9C1261E2C`.
- The first span's native open, independent visible-state proof, clean begin/end
  gates and close/drain sequence passed. Reaching the `zg361b2.40` wait gate is
  the direct live proof that the previous Python cleanup fix crossed its RED.
- The B2 wait gate is GREEN at `date_raw=53147040`, event instance `13`, player
  `29037`, owner `32904`, three shown/enabled options. No option selection was
  submitted because semantic validation failed first.
- Managed cleanup is GREEN. R534/R535 are terminated and CK3, FFmpeg and
  injector inventories are empty.

Artifact SHA-256 values:

- plan: `1FE14521B09860F24B45583160248F3C32EE90AE76FCEFB4E38548FB7B1820CD`
- outer report: `BEC09494C80BDFA5AD2A4B4E72FEB55DBD22187442D7A9D05AEBD9BE34079B11`
- inner report: `9944C0CCD7FC7535F8991831C5F61F1B0495DF8EDB63D67C7688F9A923638986`
- scoreboard visual action cell:
  `DBCC60D4297E5CA07C1C3C3B9676DF8BAC3AB723835C76470DF17612F0F95310`
- B2 action-cell RED:
  `8643CA31F0E0C6C66404BD8B6769F1EA7268DF1F5440D3361E71B44E63FF4C27`
- exact `zg361b2.40` wait gate:
  `D3928CEC881D5583718923CC3B7D5EC2CC576888E582CF83715E99155F436158`
- cleanup: `9BBB8183E47D80804C82D83E3BFE1FC528E0F0D9E80874F5269791C728B95348`
- timeline: `BD995F7275C64C4787F33D749D10EDD30035949A81C68939E8E3BC3D35EA4AB0`
- evidence index: `9DE46EA372C28A2A7E798092D8E351EE93559C70B21D326C9A0081FB35A2AA07`
- failed 25,134,069-byte MKV:
  `605B4948E1F0F2B1E05F7D051E11FB53A25C51AC066A62748DE3AA5328F9668E`

## Minimal correction

The B2 action cell's existing exact semantic allowlist now uses the current
generated English and Simplified Chinese option values for all three actions.
The order, option numbers, event identity, owner/subject/case binding, requested
action and postcondition rules are unchanged. The product event, effects,
localization generator and generated localization do not change.

The focused live-artifact comparison confirms all three observed option names
now normalize to an allowed value. The action-cell unit module passes `12/12`
and the dependent three-action save/restore matrix passes `11/11`. No CK3 retry,
long run or broad suite was used for this correction.

This changes an internal Python acceptance allowlist and its documentation. It
does not change MCP schema, protocol, data format, version, dependency, native
ABI, mod behavior or open_kaishek, so no companion synchronization is required.

