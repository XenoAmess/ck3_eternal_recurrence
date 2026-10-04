# Episode04 P0-MOVE exact-build native review

2026-10-04. CK3 1.20.0.3 / Steam build 25652598, installed EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`. This lane read files only. It did not launch or attach to CK3, access SDK/pipe/screen, advance a game day, deploy a DLL, or modify the main checkout.

## New static findings

`CHaltUnitsCommand` remains a distinct command, rather than a flag on `CMoveUnitCommand`. The current PE's RTTI identifies primary vtable `0x476B070` and secondary vtable `0x476B108` with subobject offset 24. Constructor `0x296A1B0` initializes kind at `+0x20`, and deep-copies the native int array at `+0x28/+0x30/+0x34` using `0x9E3790`. Command size is `0x40`; the source array is full generation-bearing public CUnit IDs. The current GUI's `Army.GetOrders.GetHalt` command has its single-army `halt_button` at window_army.gui lines 1119–1125, visible while moving and not gathering, enabled by `IsValidCommand`, submitted by `PostCommand`. The native getter builder at `0x1342600` allocates `0x40` and calls the constructor with kind 1. Existing command submission uses the ordinary player channel `0x0E`.

Validator `0x296A2F0` traverses IDs and returns true when **any** member passes owner-character `0x29675F0`, movement `0x24AC1B0(unit,0)` and Halt eligibility `0x24AC2B0`. Executor `0x296A260` traverses **all** members, resolves full CUnit IDs, calls Halt destination `0x24AA750`, and invokes `0x24ABBE0(unit,destination,2,0)`. Therefore a reusable public capability should accept one CUnit at a time. Sending a mixed list would not match a per-army eligibility claim.

Halt destination `0x24AA750` reads native normalized current-edge progress with `0x24AB2F0`, compares it to loaded global `0x5C699E8`, and uses **strict greater-than**. The `jle` branch uses the current province; the greater-than branch resolves the first stored path province. The exact installed stock define is `MOVEMENT_LOCKED = 0.5` at common/defines/00_defines.txt:641, SHA-256 `8e430d77eb6e8767030f34b1c53d5dae84277fb354bd73cc42f93dc500be8982`. The simplified Chinese concept's wording is less precise than the native branch. A statement about exactly 50% must follow the native predicate, rather than the translation.

Plan/apply at `0x24ABBE0`→`0x24ABDB0` preserves the existing first ProvinceInfo while locked, clears the remaining path, and reinserts the preserved first entry. It retains accumulated progress if the new front matches the old front (`0x24ABF8F..0x24ABFAC`). Thus the predicted static Halt postconditions are:

| Before | Native action scope | Required independent after-read |
| --- | --- | --- |
| Current-edge progress at or below loaded cutoff, nonempty route | Halt may clear the route after ordinary validator admission | Same CUnit and province; complete empty route, move target null; state may update asynchronously, so record actual state rather than forge immediate idle. |
| Progress above cutoff, old front differs from old tail | Halt may remove the suffix while preserving current edge | Same CUnit; route exactly `[old_front]`; no claimed immediate arrival. After natural travel, observe the front province and empty route independently. |
| Progress above cutoff, old front equals old tail | Native Halt eligibility returns false | Preserve validator rejection; do not label it a failed cancellation provider. This includes a single remaining hop and any route whose first and last province happen to coincide. |

`0x24AC2B0` also rejects unit subtype/state conditions, retreat count, missing Army identity and applicable combat-withdrawal disallow conditions. The provider delegates these conditions to the original validator. The preceding table is not a complete movement legality policy.

## Existing getters to reuse

Use `ck3_take_snapshot` for complete stored route, target, province and state. Use `ck3_query_army_strengths` for each row's `current_movement_progress.normalized_edge_progress` and `first_route_edge_remaining_duration`, native Q100000 values. This reader is independent of AI coordinator assignment. The optional reinforcement-assignment getter remains conditional on coordinator/subunit bindings, so it is not required for this episode.

Use advertised `ck3_execute_step` literals `preview-move-army-<ID>-to-<province>` for legality/path and `query-route-contact-horizon-v1-<ID>-to-<province>-h-<count>-<sorted-full-hostile-IDs>` for current native route arrival dates and the next-day contact window. There is no named preview-move or route-horizon MCP registration. Derive IDs and public revision fresh from the actual case; historical Robert IDs are examples, not William action inputs. Preview does not publish ETA. The `h` component counts hostile IDs, not days.

The timing provider already deducts matching current-edge accumulated progress in native duration calculation. Published route arrivals round Q100000 days to the nearest whole day: `(duration_raw + 50000) / 100000 * 24 + date_raw`. They are predictions; actual arrival is an independent province/state/target/complete-route observation. The existing Robert 2610 case predicted seven days and was observed arriving after eight days. No exact native arrival-update tick is established here, and an old ETA must not be refreshed by subtracting days.

## Frozen proof files and limits

`HALT-RTTI-LOCATOR.json` identifies the type and vtables. `HALT-SPANS-296a1b0.json` contains constructor/destructor/validator/executor/clone; `HALT-CALLERS-296a1b0.json` contains the sole instruction-boundary-verified constructor caller; `HALT-SPANS-24aa750.json` and `HALT-SPANS-24ac38a.json` contain destination/eligibility/plan/apply. Every bounded native span carries its own bytes and SHA-256 under the exact EXE SHA. `STOCK-MOVE-LOCATORS.json` binds GUI/localization/stock define source hashes. These are exact-build static and locator evidence, rather than live action evidence.

The external candidate02 adds an advertised `halt-army-<ID>` literal through the existing execute_step surface. It returns `halt_submitted`, never a fabricated stopped army. Eleven existing files have proposed changes: military header/source, game_contract and game_adapter header/source, native adapter, semantic worker header/source, bridge dispatch, Python war_contract and native_driver. No new named MCP tool or service convenience is proposed. The focused fixture passed real new C++ submit code with a caller-owned mock constructor/validator/queue/cleanup, and real Python grammar/advertisement. It does not test the original game allocator or original game executor. The main-thread worker, full DLL build, deployment and live postconditions remain Root's work.

Candidate01 is a preserved earlier draft with an incorrect route advertisement field; candidate02 corrects that field to `route_read_status`. No test result is assigned to candidate01. A GBK console encoding failure occurred after STOCK-MOVE-LOCATORS.json was saved; the preserved file was subsequently inspected with UTF-8 console configuration. It was an output environment failure, not a CK3 capability failure.


## Root integration, 2026-10-04

The original command is exposed through the existing execute-step grammar as `halt-army-<public CUnitID>`. `halt_submitted` means native queue submission only; the next paused snapshot must independently establish the resulting route. The focused offline lifecycle fixture and Python advertisement check passed at `C:/ck3-war-episode04-research-20261004-a01/move-control/focused01/RESULT.json`. Full DLL/worker link and new live footage are pending.
