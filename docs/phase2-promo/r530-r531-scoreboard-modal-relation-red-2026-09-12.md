# R530/R531 scoreboard modal-relation RED (2026-09-12)

## Verdict

R531 used the fresh visible-entry-parity DLL and returned the same stable
received scoreboard surface: modal, panel, received entry/tab/page and both
close controls were effective-visible; other entries/pages were hidden and the
received list ACL was available. The entry/page correction therefore worked as
designed, but the query still returned
`unavailable/state_projection_unavailable`.

The closed observation had already built the same tree successfully. In the
open observation every typed field, ACL value, unique entry and matching unique
page satisfied the updated semantic rules. The only remaining state-dependent
gate was the requirement that the GUI modal receiver vector's absolute top be
the scoreboard modal or one of its descendants.

That requirement is outside the frozen capability boundary. The ABI records
modal top relation as a provider-private input-routing diagnostic, while
`modal_blocking` remains explicitly unavailable and action admission belongs to
the independent exact dispatcher. A different absolute top receiver does not
negate the directly observed effective-visible scoreboard surface.

P1 remains `9/9 GREEN`. P2 remains `0/8`; the failed 6.59 MB take has no
qualified clean span, so editing, export and publication remain gated.

## Rounds and cleanup

- R530/PID `203996` completed the isolated, no-injection Frontend warm-up and
  terminated before gameplay.
- R531/PID `180472` was the sole gameplay instance on CK3 `1.19.0.6`, using the
  isolated userdir, `-loadsave=autosave`, bridge
  `4115E09DE9B8D234074B5AC5FA6AEB376A2AB9EB8A82609364BF475D182F3F84`
  and injector
  `91EACCC416E2D544F93D15ABD55A0FB8AEDAB205270BA11571E9F417113D8929`.
- The runner stopped on the first material gate and did not attempt the other
  seven spans.
- Cleanup is GREEN with zero failed checks. R530/R531 are terminated and CK3,
  FFmpeg and injector inventory is empty.

## Minimal correction

The provider continues to read and classify modal top as none / exact modal /
strict descendant / other and includes the relation and receiver pointer in its
private semantic bytes. It no longer cross-gates this routing diagnostic against
the scoreboard modal's effective visibility. An unreadable or cyclic parent
chain still fails the query, and entry/page consistency remains strict.

The native fixture now proves that a stable open received surface remains
available when the absolute top receiver is an unrelated widget. This directly
covers the removed overconstraint. No public response field, type, enum, tool,
capability, ACL, action, allowlist, version or readiness definition changes.

Focused validation only:

- native scoreboard state executable: exit `0`, SHA-256
  `F6A69EDE4130344E3A0CD7CEE923BA298E5D3CC59472A1FB58B37D486F124119`;
- Python scoreboard state/action contracts: `17 passed, 22 subtests passed` in
  `0.79s`;
- ABI JSON parse and `git diff --check`: GREEN.

Root `69194e654e2d9bd11bc21f58d28b23f6f28756c8` and open_kaishek
`3c6b8b2590788801fb54ef588a7568f67712627a` are pushed and synchronized.
The companion sync is documentation-only. The next live action is one fresh DLL
and one bounded R532/R533 verification; the R531 DLL will not be retried.

The fresh synchronized-root Release build for R532/R533 is GREEN from root
`73118a285878ca19e229084297d3d8a43ef1fcb9`. All 27 candidate switches are
OFF. Bridge SHA-256 is
`3D41E88ABB0FD5CF812D67CB233D2BFD7A01A7661358E7D9375BCFD31E23CF48`,
injector SHA-256 is
`6A4E7A045F54771BB027AC8E0B89B6BE131A62D99BCE239CC28BA0A9C1261E2C`,
and focused-test SHA-256 is
`6185691B7B9BFA99D3C0620A9AF6C08D56A173768A8D0D20DCAFB05A5A992BEB`
with exit `0`. Receipt
`B7BA2A35301A2EDCFB41CF538BDF79A677F6385A444CFB9183237600CCF621F9`
records no CK3 launch or round consumption.

## Evidence

- no-launch plan: `21FAC0B551DA0FBDCF614600E5A23F10E0CBAA128F13F18FB29BF7B036888988`
- outer report: `E017232C5C2FE3393B91E4A8F09AB6ECB4031B62742C655DA78ED588BCF32602`
- inner report: `2CA76B4AD9FFEBBEDEF18083CACA9FD619287A971DD5FA40F2EF137AE85DDA26`
- visual action cell: `62AC450A99AC2F8975BC723B5A4DE4B06CD03F904AF2EA4B07B44A613FF1ECC6`
- cleanup: `6B5F880BABCBCAA9DDD06DCA36BA01A7195F869071B52FC4D2C4DBC376FB408B`
- timeline: `E3384731D25794D6C7481F2813674CB833EED531CC177ADC49E81A72AC84ADE8`
- evidence index: `98AFAD4AA322DA1A3DB1FCA66D928C2EB44EC3AB93C4196963C145FA4567377F`
- failed MKV: `07D5FA575C468EB699DA8CB36E76FD432679E2DC9BB2F387F14B5038B77F7DCE`
