# Private paused sway target read v1 (2026-09-29)

Status: **source and Release build ready; no CK3 live read yet**. This package
connects the already exact-build-bound SCHEME4/9/10 observation and native
Can Send reader to the existing paused application-main mailbox. It adds the
default-off `query-active-scheme-sway-target-v1-private-<full-character-id>`
step and an explicit Python opt-in. It does not advertise a public query or
action, submit a scheme, or change normal strategy selection.

## Why this candidate

The H3911 Robert readback identifies player **29829** and direct landed
vassal **32716**, already seated as steward. Swaying this ruler has a plausible
realm relationship benefit, but current opinion and actual `sway_interaction`
legality have not been read at H3911. Therefore the first bounded run must
query target 32716 on a paused H3911-derived paired frame. A positive native
Can Send alone is not yet a strategy value judgement or action authority.
The query can then be repeated for another observed direct vassal if this
target is native-illegal or already covered by an active sway scheme.

R0325's independent family readback shows Robert actor 29829 and Emma 37265,
both with a zero high generation byte. The SCHEME10 resolver formerly
rejected generation zero before its two exact object `+0x18` full-ID
round-trips. This package removes that assumption and verifies the zero-byte
case in the normal and optimized SCHEME10 fixture. It still requires the full
32-bit identity to match the native object twice on the same paused frame.

## Read and result boundary

The private transport takes the published native revision and one target ID.
The existing mailbox verifies the paused owner thread, then SCHEME4 reads
the current player's active scheme container. SCHEME10 constructs
`sway_interaction` for the current player and selected target and asks the
exact complete Can Send validator. The response carries one copied frame:
revision, pump epoch, container generation, date, actor/target, active count,
matching active sway, native Can Send, and `native_legal_now`. A false Can Send
is classified only as `native_complete_validator_rejected`; it is not
misrepresented as a specific `is_shown`, validity, or `can_start_scheme` leaf.
The caller verifies the paused actor/date again after the read.

The Python caller must opt in with `allow_private_active_scheme_sway_query=True`
and call `query_active_scheme_sway_target_private_v1`. The normal autonomous
turn has no sway proposal or action. The next stage needs a real value input
(including current opinion), a fixed formal target, one typed submit, a fresh
owner/type/target scheme-instance readback, next-turn consumption, and paired
cold recovery. The existing SCHEME8 harness supplies raw-first attempt and
receipt accounting once a concrete target and checkpoint are frozen.

## Verification and limits

- Baseline: origin/master `d459ff4d493eab33459a9b406c39efcaa163a992`.
- `xar_ck3_bridge` Release compiled with only
  `XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1=ON`; local DLL SHA-256
  `FE2910B5621C236ACDABDDA8C7CC9E9510513D3B42A3C4BBC1061CCEF407BB08`.
  This is a source/build check, not an official Robert paired candidate.
- SCHEME10 normal and optimized `/W4 /WX` fixtures GREEN, including a
  generation-zero character precondition; private Python transport 2 tests
  GREEN. No new game action or date has occurred.
- H3911 exact paused `sway_interaction` legality, opinion, scheme instance,
  value, action receipt, next turn, and cold restore remain **unobserved**.

The local worker may request the unique CK3 slot only after a fresh master
sync, full candidate build, official pair/no-launch check, and coordinator
assignment. The game stays minimized while the paused query runs.
