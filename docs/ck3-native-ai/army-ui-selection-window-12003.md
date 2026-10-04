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


## 2026-10-05：R0162 独立 subject、可见面板与原图

最初 Army0在1506/sieging3：select ACK之后独立query已读subject_available=true、public0/native0、owner33388，但army_window完整288节点全hidden。它证明真实身份读回，不能算面板已打开。后来raw53147376 main0已实际到1513/regular1；重新原版select之后独立query visible=true，subject/owner保持，完整323节点、不截断。唯一可见 supplies与attrition父容器路径由该次实际树重新解析，不固化跨run路径。

Root直接审阅1920×1080原图 `frames/arrived-army-panel-r0162-a01/desktop.png`（SHA3035050dcd8adc9bfc7eca4cf44a4c99d5f0f200340492529e7bd4b913884d84）：军队2413、损耗0%、补给82/100与下降箭头。它只证明这张当前原图，非整片观看。鼠标仍在Lewes生成的移动候选ETA9天不能当已经结束的主军路线ETA。native stock82.99737与GUI82是同一实际案例的两种显示精度。

独立检查与像素来源在 `C:/ck3-war-episode04-research-20261004-a01/army-ui-live-r0162-a01/ROOT-DELIVERY03.json`。初始hidden和后续visible均保全。原版AF9000→AFB630只读解释已闭普通view6/combat view1A，精确sieging3→SiegeWindow分支仍未闭，不能先断言状态分支或ABI端口失败。此轮未生产Army tooltip完整文本、GUI更新epoch或hover/leave原图；P0-TERM十一项提示仍未全部拍齐。
## 2026-10-05 Army tooltip 最小提供者

在R0162的普通Army面板可见证据之后，新增 `ck3_hover_army_tooltip_v1`、`ck3_query_army_tooltip_v1`、`ck3_leave_army_tooltip_v1`，仅覆盖exact 1.20.0.3的 `supply_state` 与 `attrition`。使用原版hover setter `3AA6040(context, target/null)`，从完整当前Army树解析所属控件；公共Army ID 0合法。

hover返回绑定当前连接、日期、full Army/owner/root/source及owner epoch的原生nonce。另一次query要求相同source为实际unlocked tooltip top，读取实际唯一可见 `TooltipText` 的完整UTF-8 cache两遍并保全字节/SHA。leave返回新nonce，另一次query确认所属source消失、先前实际观测root隐藏、同Army仍在。它不直接写hover指针，也不关闭Army面板。

GUI更新epoch producer仍未查明：`gui_update_epoch=null`、`text_refresh_verified=false`、`rendered_verified=false`及nested `available=false`保持，实际cache单列为 `observed_cache`。后来一次application owner turn不能替代GUI更新或像素证据。Root在下一轮用新鲜snapshot确认玩家存活、无事件，并以真实画面另行核对文字；这些现场前提不能称为provider新增的独立完整门禁。

最终native06与Python01 patch分别为 `196e1901400f8613688c8e0135d61a4bc31833a60f342874bf9b926637829acc`、`b791f68c621d466128287adf43a77c403d0aac626e1cd535913010cd0ad2f305`。外置候选、actual synthetic producer/mailbox检查及独立peer保存在 `C:/ck3-war-episode04-research-20261004-a01/army-tooltip-provider-a01/`。Root合入两个patch及safe-pause后，主树70项UI focused与16项pause focused通过，记录在 `root-code-checks-a01/`；Endpoint/local buffers不构成真实CK3 tooltip验收。正式DLL构建与下一次隔离实机另记。
