# H3928 family companion: paired no-launch candidate (2026-09-29)

Status: **official paired no-launch ready; no new CK3 frame or family action**.
The exact game remains CK3 `1.19.0.6-steam23530548`, EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The native decision and result boundaries remain in
[marriage-and-alliance.md](marriage-and-alliance.md), and the first-heir
relationship reader remains private.

## Why this H3928 frame needs a read

The original H3928/raw53219928 sidecars for actor 29829 and episode
`native-29829-2bc2d599f7f9` contain two different family states:

- First heir 38822 and candidate 38718 have a **resolved betrothal** with
  `material_result=true`. This does not establish an alliance or adult marriage.
- Player child Emma 37265 to Gerard 37267, recipient 32440, remains
  `receipt_pending` with `material_result=false`. Sending this proposal again
  would duplicate an unresolved action.

The merged #663 companion path reads the child result and current primary
first-heir relationship beside it in one paused native frame. It does not
evaluate or submit a new marriage. Source inspection found no additional
reproducible missed family consumer on this H3928 frame. The relevant next
evidence is the exact pending state and first-heir relationship from CK3.

## Frozen candidate and pairing

The [candidate index](<Z:/family-h3928-companion-v2-20260929/CANDIDATE-INDEX.json>)
has SHA-256 `6E6044002DD4A0238FE1CE6A8E662825F2984BA866E4B298896DCB2BA78999C4`.
It binds exact master `74d58efc9df8ca319f276ea2eae415e2ea450a8e`
(official push CI `36572566634` SUCCESS), Release DLL SHA-256
`A6D749B576F2E8543F2121CE0352762D39EBC061C749DED6782CA5A80E75041A`,
injector SHA-256 `7160ACA19FC5D23B8B0239A19101105E450B1D7AD91FAAC20AC8C9FC6B38A3E4`,
the original H3928 save SHA-256
`A92073407D1CB2800EEF9C0C3EFEB9846D48398F679DC3163B71EF86C40CEC2C`,
and its official rebind of the paired driver and family/Sway sidecars. The
candidate's Z-drive preparation script has SHA-256
`E212A1AFF00737BD774D36549173A47EAC6F4C632F17C64ADEDEE7F4647FF663`.

Official [no-launch report](<Z:/family-h3928-companion-v2-20260929/state/preflights/20260929T132943Z-one-generation-preflight-04d310ac/report.json>)
SHA-256 `F209097FB74736CCA09F77BC646DA2F4CF8267FBE1E95E9F9BDD1D9D984410A1`
returned `status=ready`, `ok=true`, `ck3_launch_attempted=false` and an
empty local process inventory. The prepared driver SHA-256 is
`D22186105142B81B815CA500E618A61668ABD63A6BA8BE853CDB877C58660E05`.
The source save remained byte-identical. This is a no-launch result; there is
no new native revision, proposal response, date advance or material outcome.

The single-instance owner can take this indexed candidate into the existing
queue. Its indexed operator arguments request one child pending read for
37265/37267 plus the first-heir companion, with zero proposal/action/date.
Before that run, verify current PID/owner and the frozen index/manifest; after
load, minimize the window. An unavailable or frame mismatch stays RED. The
live result must report the child pending/resolved status separately from the
first-heir relation. Any later gameplay turn and cold restore require their
own paired evidence. This candidate is separate from PRV008 and does not
expand its qualification or change G2's `3/8` count.
