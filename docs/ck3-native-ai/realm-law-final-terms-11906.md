# Realm law final legality and numeric cost, CK3 1.19.0.6

Status: **exact-build static-ready, private read only**. No CK3 instance was
started for this work. No H3911 law, cost, or legality was observed. The
executable is `binaries/ck3.exe`, 95,206,008 bytes, SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The machine proof is
`ck3_autonomous_player/native_bridge/research/realm_law_final_terms_11906_abi.json`.

## Why this read is needed

The legally paired H3911 Robert driver state has `feudal_government`,
`government_uses_crown_authority`, and `split_successors`. Its held-title
partition sends county `2173` to character `38988`, while the primary duchy
`2141` and other titles first go to `38822`. The latest campaign-root query
does not publish the active crown law, a candidate's final CanEnact, or its
native cost. This gives a specific governance decision to observe; it does
not establish that changing a law is legal or beneficial in H3911.

The original tree and scripts are described in
[laws-contracts-and-succession.md](laws-contracts-and-succession.md).
`common/laws/00_realm_laws.txt` says `crown_authority_2` grants
`can_change_succession_laws` and changes vassal tax and levy contributions.
The crown authority pass cost is scripted prestige. Whether a target law
changes H3911's successor split remains an unobserved outcome and cannot be
inferred from the script flag alone.

## Exact same-source native path

```mermaid
flowchart TD
  A[GuiLaw.CanEnact 0x3DDF770] --> B[validate captured played character identity]
  B --> C[CLaw kind gate 0x2C7E900]
  C --> D[already active 0x28BC040]
  D --> E[engine final evaluator 0x2C7D930]
  E --> F[build ten-slot numeric cost 0x2C7E490]
  F --> G[scripted cost evaluator 0x2CDB7B0]
  E --> H[engine affordability 0x2CDCFF0]
  I[GuiLaw.GetShortCostString 0x3DDF860] --> J[format cost 0x2C7E5B0]
  J --> G
  K[per-component can_have / can_pass names] -. unknown .-> E
  L[paused H3911 active law / cost / final result] -. pending live .-> A
```

`0x3DDF770` checks the captured full-generation player ID, resolves the
current character, requires its law context, then calls the type gate,
already-active check, and `0x2C7D930` in that order. A direct call to
`0x2C7D930` alone does not reproduce the complete GUI predicate.

Within `0x2C7D930`, the sequence at `0x2C7D9DF..0x2C7DA0A` passes
`CLaw+0xCD8` and the actor's full ID to `0x2C7E490`, then passes the
resulting 80-byte vector to `0x2CDCFF0` for affordability. The numeric
helper first builds the same native script context as the GUI formatted-cost
path via `0x98C0F0`, then calls `0x2CDB7B0`. The latter evaluates ten
compiled cost rows at `cost_block+0x38+i*0x108`, accumulates signed Q100000
amounts, then applies its authored clamp/round flags. Do not recompute a
scripted prestige formula outside that engine path.

The ten ordinals use the already frozen generic cost mapping in
`pending_character_interaction_context_v1_abi.json`: gold, prestige, piety,
renown, influence, herd, treasury, treasury_or_gold, merit, barter_goods.
Slot 7 is routed to treasury or gold by the engine; it is not another
independent balance. The current LAW2 value type has a six-entry cost array,
so production registration must preserve the complete native vector and
represent slot 7 correctly. A six-slot projection would lose cost terms.

The new `realm_law_final_terms_11906` reader is a one-callback private seam.
It receives freshly resolved native law and actor pointers plus actor ID,
replays the three GUI gates, and copies all ten numeric cost terms. It does
not retain pointers or submit a command. Its operation table must be bound
only after the exact ABI proof and inside an application-main paused query.
The existing LAW2 source adapter remains responsible for frame consistency,
two samples, title baseline, and value-only publication.

## Readiness and unresolved fields

The engine final Boolean includes compiled trigger and affordability checks.
Three compiled trigger objects at `CLaw+0x398`, `+0x558`, and `+0x638` are
evaluated by `0x2C7D930`, but their individual `can_have`, `can_pass`, and
realm applicability names are not yet proved. `GetCanEnactDescription`
ultimately uses the command validator with an engine-owned error sink; its
safe copied reason format is also unresolved. The private reader therefore
reports an opaque engine-blocked status and does not fill LAW2's separate
component or reason fields with guesses.

Next, register this read with the candidate collection from
[realm-law-active-collection-11906.md](realm-law-active-collection-11906.md),
close the component/reason ABI only if needed by the current decision, and
run one matched, paused H3911 observation. Record active law, all relevant
candidates, full costs, final CanEnact, and the same-frame resource and
successor baseline. A read-only result is still not an enactment receipt.

## Private paused query candidate (2026-09-29)

The default-off `query-realm-law-final-terms-v1-private` step now binds the
current full-generation player character through the exact component storage,
then visits only the two frozen feudal law groups. Each candidate is evaluated
on the application-main thread by the GUI type/active/final path and the
ten-slot numeric cost helper. The same command validator at `0x2C7DAA0`
copies its engine reason into an engine-owned MSVC string sink; the native
destructor at `0x7E97D0` releases the sink after copying. The collector takes
two complete samples inside the same paused callback and rejects any key,
membership, final status, cost, or reason difference. The pipe handler also
checks the published frame and its revision before and after the callback.

```mermaid
flowchart LR
  A[paused current player and revision] --> B[main-thread mailbox slot 56]
  B --> C[exact ABI and full-generation actor]
  C --> D[crown and succession candidate groups]
  D --> E[final CanEnact and ten native costs]
  E --> F[command-validator reason copied]
  F --> G{two samples identical?}
  G -->|yes| H[private value-only result]
  G -->|no| I[RED]
  H -. no law command .-> J[future strategy/action gate]
```

The CMake option is OFF by default. The Python one-shot operator opt-in exits
after this read without submitting a law command or advancing a date. The
result retains all ten signed Q100000 slots and reports current active key,
candidate key, `final_can_enact`, status, and copied reason. A blank native
reason remains blank; it is not replaced by a guessed script cause. H3911 and
the newer H3922 paired Robert frame have **not** been queried with this build
yet, so no current lawful or beneficial enactment is claimed.

The exact-build binder currently uses the published mutation ABI proof for
the command validator and final evaluator, plus the pinned EXE identity and
the numeric helper ABI in `realm_law_final_terms_11906_abi.json`. The private
query does not fill the old six-slot LAW2 schema or advertise a public law
action. A later formal decision must compare the observed successor baseline
and resources with the candidate value, then submit and independently read
the enacted law and successors.

The focused normal/optimized MSVC candidate fixture is 8/8 in each mode;
the private route builds with its option enabled in VS 18 Release. The
no-launch Python transport checks full ten-slot preservation, frame change,
and default-off gating. These are source and fixture evidence, not live proof.

## Focused verification commands

```text
py ck3_autonomous_player/native_bridge/research/verify_realm_law_final_terms_11906.py --exe "Z:\ck3_mod_rewrite\Crusader Kings III\binaries\ck3.exe"
py -O ck3_autonomous_player/native_bridge/research/verify_realm_law_final_terms_11906.py --exe "Z:\ck3_mod_rewrite\Crusader Kings III\binaries\ck3.exe"
```

The verifier checks exact EXE identity, the six native spans, exception
entries, seven relative calls, and the independent native resource-ordinal
contract. The standalone C++ fixture compiles under MSVC C++20 `/W4 /WX`
in `/Od` and `/O2`; it covers legal, kind-rejected, already-active,
engine-blocked, cost-read failure, and absent-operation cases. These checks
are static/fixture evidence only.
