# Army selection and window — CK3 1.20.0.3

2026-10-04 / W40. Exact EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`, Steam build25652598. This is an **Army-only static-ready** migration of existing typed MCP query/select. Actual window, tooltip and capture verification remain separate milestones.

R0161's actual `ck3_select_army_ui_v1(subject_army_id=0, expected_revision=3)` returned `capability_not_available`. Its frozen f853 adapter omitted the UI family; enabling an unrelated CMake flag would not supply a current implementation. The original failed packet is retained under `C:/ck3-war-episode04-research-20261004-a01/native-live-main-case-a01/responses/show-army-zero-a01.json`.

The existing `ck3_select_army_ui_v1` and `ck3_query_ingame_ui_window_v1(window_kind="army")` now use the exact current-version producer and original paused owning-thread mailbox. Character/combat/knights operations remain bound to their existing build; a .3 request for those roles is rejected before dispatch. SDK registration alone does not prove native availability.

| Current original source | Contract |
| --- | --- |
| `SelectUnit` registration09D6B0 → D1CA50 → D18870 → AF9000 | Original `void(handler*, full public CUnitID, bool replace)`; public0 is valid |
| Idler root5C6A520; RTTI5514438→5514460; idler+88; handler vtable44BA890 | Current ingame handler, reused from the exact .3 binding |
| B0F1E0; handler+98+view6*8 = handler+C8 | Current ArmyWindow slot |
| ArmyWindow TD57769C0, constructor1345180 | Exact current window type |
| GetArmy13509A0→13463F0; window+C8 | Current native Army full ID, distinct from handler+C8 |
| Army storage5D1DE48, Army+124; Unit storage5D1E380, Unit+178/+174 | Complete-generation reciprocal public/native join and actual owner |
| window+60 == named army_window root; window+A0 == handler | Bind the native window to its actual GUI root and handler |
| GUI+D0 effective-hidden08 / disabled02 | Existing current GUI visible/enabled observation, not a selected-ID proxy |

The producer rechecks window/subject/owner/root/visibility at the end of the read. Owner comes from the same joined Unit; .3 exposes `owner_character_id_available` and explicit null when unavailable. A failed panel pre-read clears partial panel observations. Original SelectUnit can open a not-yet-created window; its immediate response is `acknowledged_verification_pending`, never proof that selection or pixels changed. Only a later independent query can establish the selected full ID, actual owner and visible bound panel. The existing current GUI census allows2048 nodes; legacy Python retains its512 bound.

Two peer-review findings in candidate06 were corrected in candidate07: default owner0 was replaced with actual owner/availability, and failed pre-read panel fragments were cleared before ACK. Candidate06 and all failed compile/plan attempts are retained. Current producer lifecycle fixtures, mailbox/adapter compilation, exact ABI peer review and Python fixtures passed. Root's combined main-source integration ran51 UI tests and11 generic-preview tests once, all passed. Synthetic fixtures execute no CK3 originals and add no game days.

Current generic read-only `preview-move-army-N-to-N` now uses the existing native preview capability for canonical ordinary ProvinceIDs as well as strategy-advertised objectives. The former Python filter rejected1513 before reaching its already-generic native provider; London1527 worked. Native paused/full-ID/controllable/province/move validation remains. This preview correction does not itself authorize generic typed move destinations: the separate `ck3_move_army` strategy-list filter is being repaired in its own package. A preview is a prediction, not an order or arrival.

Frozen evidence: `C:/ck3-war-episode04-research-20261004-a01/army-ui-native-port/ROOT-DELIVERY02.json`, native patch SHA `c3cbd6f5c2bc00234c60e8077ba039a095369bc86de23d224e44574e22891084`, Python patch SHA `9bee865c1c782993db016fefe6274184ea24dd854d0c1cf62822c0f2989fa3f3`; independent ABI/peer report at `army-ui-readback/peer-review-a01/ROOT-DELIVERY.json`. Generic-preview patch SHA `1bf3481ab3894cd15b81dc4ce5b02f88445f8d20b30a05f4c6544b8732d0e349`; original error and source diagnosis remain in `preview-generic-province-a01/`.

Next actual sequence: new clean source/strict DLL and fresh offline lease → cold-load independent save → paused snapshot → select the actual player full CUnit once → independent Army query → original screenshot with exact geometry. Record actual owner/selected ID/visible state and screenshot bytes. General supply/loss tooltip hover and active-tooltip text binding are not supplied by this migration; their exact native chain is under separate research. No desktop fallback, tooltip claim or human video signoff is inferred from this package.

## Typed ordinary-province move correction — 2026-10-05

The separately diagnosed movement filter is now corrected in the existing `ck3_move_army` service/driver path. An explicit request requires the native movement and complete-route capabilities, fresh paused ready map, living actual player and owned controllable full CUnit, and no combat/retreat. Original native ProvinceID, character/army/move validators remain responsible for actual eligibility. The existing native submit and independent route observer are reused; no Halt is issued as a side effect. Source date, actor, full army, connection generation and episode must still match after the one command. ACK without an actual moving/arrived route is rejected.

Strategy-advertised action targets and raw `execute_step` move literals retain their existing scope; the typed input now expresses the already-generic native command directly. Fourteen focused service/driver/registered-MCP cases passed, including a non-advertised1513 target, original native rejection and ACK-without-route. This is a pure Python change and requires no new C++ producer or DLL. Its first actual ordinary-province move remains pending in the new independent run. External patch SHA `98cd49286e18c3037adb7bec3e951ad2fb685618f4af23de80358518b7233c50`, receipts at `C:/ck3-war-episode04-research-20261004-a01/move-generic-province-a01/`.
