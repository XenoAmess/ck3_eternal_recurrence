# Private paused sway target read v1 (2026-09-29)

Status: **R0330 live attempt RED before native Can Send; root fix under focused
verification, no successful CK3 sway read yet**. This package
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
and call `query_active_scheme_sway_target_private_v1`. The managed
`native-auto-run --private-active-scheme-sway-target <full-ID>` route passes
that opt-in only for a bounded run, reads once on its first paused frame,
compares the source and post-read actor/date/revision, then exits before
planning or submitting a gameplay action. Its report records
`private_active_scheme_sway_observation`, `outcome=read_only_observed`, and
zero gameplay turns. The normal autonomous turn has no sway proposal or
action.

The managed Operator `run` command forwards the same explicit
`--private-active-scheme-sway-target <full-ID>` value to `native-auto-run` and
records the target in its receipt. It still performs the official paired
no-launch preflight and ownership allocation before a run; an operator receipt
alone does not establish live Can Send or any scheme action.

The action stage needs a real value input
(including current opinion), a fixed formal target, one typed submit, a fresh
owner/type/target scheme-instance readback, next-turn consumption, and paired
cold recovery. The existing SCHEME8 harness supplies raw-first attempt and
receipt accounting once a concrete target and checkpoint are frozen.

## Verification and limits

- Baseline: origin/master `d459ff4d493eab33459a9b406c39efcaa163a992`.
- `xar_ck3_bridge` Release compiled with only
  `XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1=ON`; local DLL SHA-256
  `850DF730D27B4B39CFCBF39066126E06DB72EAD71275EE9838AFF01F07E15829`.
  This is a source/build check, not an official Robert paired candidate.
- SCHEME10 normal and optimized `/W4 /WX` fixtures GREEN, including a
  generation-zero character precondition; private Python transport and
  bounded owning-thread route focused tests GREEN. No new game action or
  date has occurred.
- H3911 exact paused `sway_interaction` legality, opinion, scheme instance,
  value, action receipt, next turn, and cold restore remain **unobserved**.

The local worker may request the unique CK3 slot only after a fresh master
sync, full candidate build, official pair/no-launch check, and coordinator
assignment. The game stays minimized while the paused query runs.

## R0330 exact-build root correction

The first H3911 paired, paused read in R0330 stopped on
`native_scheme_observation_red:root_unavailable` before the sway legality
query. The immutable Operator report is
`Z:\m6swayh3911\operator-runs\sway-h3911-read-1\formal-report.txt`
(SHA-256 `0F33C7A094BB3F88A83518ED9759EC528C69364BBBBDED65D118D2FB20C00630`).
The game was paused and responsive with player 29829; no gameplay action or
date advance occurred, and the process tree was reclaimed. This is a source
binding failure, not evidence that target 32716 is native-illegal.

The binder had treated `*(module+0x570E068)` as the base of the embedded
scheme manager. Exact EXE 1.19.0.6 (SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`)
at RVA `0x25A1A63` instead reads `[game_state+0xA0]`, then at `0x25A1A6A`
adds `0xA538`; RVA `0x2EB5584/0x2EB558B` independently repeats this chain.
The corrected root is therefore `game_data = *(game_state+0xA0)`, then
`manager = game_data+0xA538`. The native fixture now models both objects,
so the earlier direct `game_state+0xA538` lookup fails the focused test.
Normal and optimized `/W4 /WX` fixture runs pass with the correction.
This does not establish a live scheme observation; a newly paired candidate
must repeat the bounded paused read before any typed sway action.

## Same-frame target opinion input (source candidate)

The exact 1.19.0.6 `sway_interaction` native AI source considers the
**recipient's opinion of the actor** and assigns zero AI weight once that
opinion is at least 100. That is the direction needed to value a sway of a
direct vassal. The already implemented `ReadGiftOpinionExact11906V1` reads
that direction from full character identities, checks the exact
`gift_opinion` definition and two agreeing native samples, and distinguishes
an observed opinion of zero from a failed read. It was previously consumed
only by the faction gift path.

The private sway mailbox now samples `recipient=target, player=actor` after
the native Can Send evaluation and before publishing the same paused frame.
Its new `target_opinion_of_actor` is an integer, including a legitimate zero;
an unavailable receiver returns `native_sway_target_opinion_red` rather than
publishing a guessed value. The Python private transport requires the field.
This is a **source and focused test candidate only**: earlier paired DLLs,
including R0331 if already frozen, do not acquire the field. A new exact
paired DLL and paused read are needed to learn target 32716's actual opinion.
Opinion plus Can Send still requires a policy value judgement before any
typed sway submit; no action or date advance is claimed here.
