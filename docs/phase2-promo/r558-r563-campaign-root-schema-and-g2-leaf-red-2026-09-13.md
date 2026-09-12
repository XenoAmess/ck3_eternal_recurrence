# R558-R563 campaign-root schema skew and G2 leaf RED

## Outcome

P2 remains **`0/8` accepted clean spans**. Both attempts closed the first two
spans, but neither produced one complete continuous eight-span take. Their raw
MKV files are retained as failed evidence and must not be used as final media.
The final promotional-video lock remains in force.

The attempts exposed two separate integration failures before any Stage 10
product action:

1. R558-R560 loaded a promotion-only bridge built from `471ded29`, while the
   Python consumer at `f39678f9` required the newer campaign-root frame. The
   strict parser correctly rejected the missing fields.
2. R561-R563 used a fresh bridge built from `f39678f9`, so the schema parsed.
   The Stage 10 source query then returned
   `direct_landed_vassals_unavailable`. The campaign-root provider's current
   all-or-nothing aggregation cleared already observed player, liege,
   government and rule fields, and the Stage 10 identity gate correctly
   refused the empty frame.

The second failure is an observed G2-to-T0 regression. It is not a new mod
business failure: the canonical Stage 10 checkpoint and v7 receipt remained
byte-identical, the restored player was CharacterID `27181`, the contracted
owner was `36354`, and no Stage 10 action had run.

## Attempt evidence

| Attempt | Rounds | First RED | Primary report | Stage 10 cell | Raw failed take | Cleanup |
| --- | --- | --- | --- | --- | --- | --- |
| `p2-capture-r558-r565-f39678f-20260913` | R558 warm-up, R559 initial gameplay, R560 manager restore | malformed `campaign-root-context-v1` frame | `D7893A8D9B7E554245D65BE967BC17EF7862819DFE807F8F6D13A5F3A1491849` | `B1B6EA563764743EC115FC20346B43EDA58C9C4B82E129EFF0BD9D253B2A0D98` | `E0BF557C510AC87E31DA39F4F257AEF81C4FEA59BBB66B5E0711832F33E1C917` | GREEN, `EA36DAAA87CE007FA8614ED5E29EC63B65CFBDEE75CA54C3CF2D5454939E4888` |
| `p2-capture-r561-r568-f39678f-20260913` | R561 warm-up, R562 initial gameplay, R563 manager restore | `direct_landed_vassals_unavailable` collapsed the full root frame | `D3327A0FF73A098B241A9EA464865CCD16821AC50F234168524C4DE921FB71D0` | `1F230609465F50126068EC6B455F22EC79AF4C974F8CC7E6A3CF41616F6D0857` | `3E0068A563654F4A4D21066CF6A919ABA504DDE11BF975BDD5B36BEF4CF769CE` | GREEN, `338D2653B7E4829717D30904566F308E1E5D68F0CA4833A96ADA819C24B69721` |

The second raw take is 79,701,430 bytes. Both cleanup receipts have no failed
checks; no CK3, FFmpeg or bridge-injector process remained after R563.

## Current-build bridge qualification

The repaired-schema promotion profile is outside Git at:

`Z:\ck3_mod_rewrite\_runtime\native-builds\p2-r561-r562-promo-schema-f39678f-v2-20260913`

- source commit: `f39678f97d034058f43f02e49ce81bbfedd788fd`
- bridge: 2,639,360 bytes,
  `DC2F2888E3E403DA9315E49006A73E8AD16E474017F95A8F90B0F1D1256C7E78`
- injector: 39,936 bytes,
  `F4D9F96AD65197E02CA996FDEE4536F820BA5191588E6361B078A220D1B2F548`
- build receipt:
  `6EB060F96BD94DB390B9254BE8A89B4167F5917DBA58341E7B0B80F316CDAF7E`
- candidate switches: 27 total; only
  `XAR_CK3_ENABLE_ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1=ON`
- focused native tests: campaign reader, campaign source contract, adapter
  registry, scoreboard state, promotion compensation postcondition and its
  mailbox, **6/6 GREEN**

This closes the first attempt's schema mismatch. R563 proves the rebuilt DLL
reaches and parses the campaign-root result.

## Minimum remediation

The P2 Stage 10 runner now passes its already validated manager-source receipt
into the action cell. The action cell still prefers and requires the full live
campaign-root identity. A receipt attestation is allowed only when all of the
following are true:

- the restored snapshot's player is the contracted manager;
- the normalized v7 receipt is GREEN and every receipt check is true;
- manager and owner CharacterIDs match the action request;
- checkpoint and receipt SHA-256 values are present and well formed;
- the source is single-player, production-only, non-fixture and non-console;
- the campaign query is unavailable for exactly
  `direct_landed_vassals_unavailable`.

No other campaign failure is carried. In particular, `lieges_unavailable`, a
wrong player, a wrong owner, a failed receipt check or any broader unavailable
reason remains RED before checkpoint save or timeline advance. The real
`zg361mg.120` event identity, saved owner/subject scopes and terminal manager
provider remain mandatory after navigation, so this change does not convert an
ACK or an offline receipt into the Stage 10 business postcondition.

Focused verification is deliberately limited to the changed Python seam:

- Stage 10 action-cell tests: **10/10 GREEN**;
- P2 runner plumbing tests: **21/21 GREEN**.

The deeper G2 issue remains open: `campaign-root-context-v1` should eventually
stop making every mature consumer depend on every newly added leaf. That
redesign is not a prerequisite for the next T0 attempt because the exact
restore and narrow attestation above remove the observed cross-priority
regression without claiming the direct-vassal leaf ready.

## Round state and gates

- Old rounds R558, R559, R560, R561, R562 and R563 are terminated.
- Current CK3, FFmpeg and injector inventories are empty.
- P1 remains `9/9 GREEN`.
- P2 remains `0/8` accepted clean spans.
- No final-video editing, export, publication or preheat occurred.
- No product tree, DLL source, MCP public interface, open_kaishek API or
  dependency changed in the minimum remediation.

