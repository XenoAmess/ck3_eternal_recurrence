# Call ally v36: downstream admission rejection after terminal executor exception

2026-10-03. Exact CK3 1.20.0.3 / Steam25652598, EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`. Actual game PID90596, Robert29829, original ordinary campaign episode `native-29829-2bc2d599f7f9`, raw date53236728. Artifact root `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v36-retry-02/actual-new-leaves-v36-01/`.

The new three ally queries did not execute their FAMILY reader. They contain MCP errors without a native structured body. This attempt supplies no picker result, selected context identity, CanSend, quote or AI answer, and cannot evaluate whether the prior [native selection-order correction](call-ally-selected-target-finalization-12003.md) repaired the original v35 identity fault. It is a shared runtime admission failure, distinct from a completed leaf returning an unavailable identity observation.

## Actual sequence and shared fault

`027` before the terminal query publishes `main_thread_query_mailbox_v1.failure=0`, `ready=true`, with published/completed/executed/started requests all12. `028` terminal transition is the first RED: `application-main typed query failed or its snapshot changed`. `029` immediately afterward publishes failure512, readyfalse, with all four counters13.

Every later snapshot `031/033/035/037/039` retains failure512, readyfalse and all four counters13. These include the snapshots immediately before and after each ally query. Pump epochs continue to increase; public snapshots and the final checkpoint remain GREEN. The executor was not invoked for repentance, holy-order or the three ally queries after the terminal exception.

The common-runtime lane and terminal lane confirmed source semantics in frozen g37: `main_thread_query_failure_executor_exception = 1<<9` at header132; executor SEH sets that bit at cpp1782; Submit rejects nonzero failure flags at cpp1433/1463; Reclaim returns the slot to idle without clearing the flags. The specific terminal exception code/RVA/getter is still unobserved. These conclusions reuse the owners' verified source mapping; this lane does not introduce another native callback repair or clear the failure flags.

| Actual packet | Recipient | Native FAMILY body | Snapshot counters before/after |
| --- | ---: | --- | --- |
| 034 | 34730 | absent; MCP text RED | 033/035: failure512, readyfalse, requests13 |
| 036 | 37689 | absent; MCP text RED | 035/037: failure512, readyfalse, requests13 |
| 038 | 38718 | absent; MCP text RED | 037/039: failure512, readyfalse, requests13 |

## Decision and postconditions

No concrete send request is emitted from this attempt. Existing war authorization remains valid; the missing input is a newly executed native per-war legality/quote observation. The native selection correction and outgoing sender remain static-ready. This attempt proves no call submission, native called marker, allied war membership, troop arrival or resource payment.

The final snapshot independently publishes gold106140557, prestige269831850 and piety37188750, each scaled100000. These are current resource balances, not a paid-cost receipt. Before a future single legal call, refresh the selected row and balances, bind its full WarID/recipient/cost quote, then independently compare same-side participant membership and `recipient_was_called` afterward. An ACK is queue submission only; `WasCalled` is the native called marker; new same-side participant membership proves joining that war, not army arrival. Compare raw resource balances for observed slots without treating quote or unexplained delta as payment. Other cost-slot balances remain unobserved, without adding a new speculative gate.

## Evidence and next owner

- `027-ck3_take_snapshot.json` SHA-256 `07a7e06db7be311e4b421682216cdd246283bb383239ee636a92bdd85f071b43`.
- `028-ck3_query_battle_terminal_transition_v1.json` SHA-256 `7642692e7fd58566f338e093d65ed0a602d3b3f274fa8ed1739b2ed9a10c1f6a`.
- `029-ck3_take_snapshot.json` SHA-256 `e5f46611b232722d8fb1681edaf04f8d04f4f118d20ac0d6bd2ed112a9ea93ea`.
- `033-ck3_take_snapshot.json` SHA-256 `e1f1ad7ee98aa59a07c35eb04e005acb2ab7b3611315e82c4a083c130dc88d72`.
- `034-ck3_query_family_obligations_private_v1.json` SHA-256 `12c5bb02038a82637958c8a017472dc28f4ed1c2b92defd839aa50323608ddb1`.
- `035-ck3_take_snapshot.json` SHA-256 `706afa765bdfd280bac44174691e179ca6cbab6745a95cfa32a4b88a88167847`.
- `036-ck3_query_family_obligations_private_v1.json` SHA-256 `add4213b3fb40027edff608b375966b8631679df3d12be47ca56d0645d957c7a`.
- `037-ck3_take_snapshot.json` SHA-256 `375f6c9b5a437ed064caa68fc77cf31d8940e6ae6c3f66fa84469b3d23b9725c`.
- `038-ck3_query_family_obligations_private_v1.json` SHA-256 `561ed3c8a958d642e6b4564c9947db143c4e4db37e914c98ef3776f75b99d020`.
- `039-ck3_take_snapshot.json` SHA-256 `04435764d891ba95ec34d665069c0f09fb34cfa52d629729e3f34a3502c838c9`.

External aggregate: `call-ally-native-action/new-v36-consumption/ACTUAL-V36-ALLY-CONSUMPTION.json`, with all13 packet hashes, exact original errors and mailbox values. The separate `postcondition/ROOT-DELIVERY.json` pins actual prestate and future postread recipes; its initial consumer KeyError is retained as a harness RED, not a native capability failure.

The common-runtime authoritative mapping is in `runtime-preparation/v36-retry-02/diag-summary/DIAG-SUMMARY.json` and `PINS.json`. Root's next plan is a normal stop/restart of the same v36/R15 build, then paused value queries/actions before any terminal query. The terminal owner handles the actual SEH code/RVA correction; the future v37 terminal query runs after saving and last in the sequence. This is no automatic rearm or new gate. This lane made zero SDK calls, query retries, tests, game/window actions, Git mutations or shared source edits. Original v35 identity failures, v36 configure RED, successful static fixtures and this failed real attempt all remain separate evidence.
