# G2 v67 部署交接（2026-10-05）

本交接按 Root 正式事实封口至 h8411 同日读回：source freeze、严格构建、首次 renderer、R40 official/cold/MAIN 已完成；Commander、NativeTick、WarAlliedSupport 三个 sole consumers 的字段摘要已齐。raised 与 mercenary composition 已达 production-live primitive；完整经济/军事 OODA 不作完成声明。

## 已确认 source 与构建

- native/Python 同一冻结树 `Z:/g72`，HEAD `56423709cc9608f0b3b2e1b9533207f35622146b`；freeze `2026-10-04T23:37:35.514220Z`，dirty 0。
- 单次 strict 4 Release / W4 WX / jobs 64：Root session36868 CLOSED exit0 GREEN，82.708561s，570 TU / 567 unique / 1111 compiled inputs。
- DLL：9313792B，SHA-256 `81b6216b6d2bb66410761b5e32d22f0117a520aa9bfa9f5a88cd85a125a60059`；manifest：271932B，SHA-256 `fbde613652056695641deb0f008145c3ae881808fcbcf34a253c43c5ada7296a`。
- candidate flags 115 = 65 ON / 50 OFF，WAR_CASH ON；保留既有 CLI，不加 native flag 或新 gate。

frozen564 的 official CI `37244381729` RED 保留：旧 army metadata expectations，compile0 / test1。后继 `e89` 仅修测试期望，唯一旧 fixture GREEN 5.24s，corrected official `37244804751` success 单独记录；它不替换 frozen564 的结果，不改本 DLL，也未重做 native build。

## 已完成的切换截点

R39 正常停止，managed controller72308 CLOSED exit0。Root file-fill 一次 exit0，renderer FIRSTONCE exit0；fullhistory 与 saveanchor 均为 h8406，完整十条流和全部失败历史保留，source 存档字节不变，nonwar=false。renderer 不传 `--source-pair`，本次 source pair 由已结束的正式状态一次取得。

- source raw date：53260776；存档 98135224B，SHA-256 `f3291550ce642b7836b84c7994568d7e387a613635d4932931374018c3602b5a`。
- ROOT-PACKET SHA-256：`1a17133bd05ebbc9feeac28a4aac2b36d113d12c20e5d1b7ec101072f281b938`。
- 正式累计 4852 日 / resume1699 / 当日 +194；部署新增 0 日。
- source state：`Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-12003-v66-20261005/state`；target state：`Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-12003-v67-20261005/state`。

## R40 已确认冷部署与 MAIN 领域读回

| 项目 | 当前纸面值 |
| --- | --- |
| official prepare / verify / stage / rebind / preflight | 全部 exit0 GREEN，stage10；R39 已 superseded |
| environment SHA | `5cc5c5acb289acec478c3be7a2d1140615d10f3968ace598773876dff6bada88` |
| R0040 canonical / execution | `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0040` / `cc9c95d7-b136-4e0d-ae8c-94a38138a7c5` |
| allocation / launch-started | 实际 exit0，具体时间 null |
| managed controller / PID | 45869 ACTIVE minimized / PID110616 |
| cold65103 | CLOSED exit0 GREEN；fullhistory8407 / saveanchor8406 |
| source SAVE | h8406/raw53260776/98135224B/SHAf3291550ce642b7836b84c7994568d7e387a613635d4932931374018c3602b5a 不变 |
| MAIN21717 | CLOSED exit0 GREEN；004strengths / 006occupation117440524 / 008mercenarycontext 三注册工具 GREEN，三 sole consumers 摘要已齐 |
| 正常 SAVE 截点 | h8411 / date53260776 / 98135202B / SHA `bc71178f3b934498c3286f12d1243ef71f723f03c6f0e7610d9838542677064c` |
| actor / episode | 29829 / `native-29829-2bc2d599f7f9`，newday0 |

MAIN 位于外置 `v67/root-results/actual-main-readback-01`；本 lane 仅使用 Root/sole consumers 摘要，未读取叶/raw/State。运行继续 ordinary365日/step24h、XAR off、nonwar=false；新 controller 最小化。正式4852日/resume1699/+194，cold/部署新增0日。后继 ordinary24 session30642 ACTIVE，结果与未来日信用排除在本交接外。

## 冷后最小读取与 readiness

默认 NO-PREQUERY 空 calls，不重复原四 Sway、不重发 Start。MAIN 仅三条：existing strengths3 → occupation War117440524 → `ck3_query_player_mercenary_context_v1` once。每 query 由成熟 capture 取得 fresh public snapshot revision；mercenary 只传 expected_revision，不 submit/hire。

g72 MCP 在 `src/xar_autoplayer/bridge/mcp_server.py:2486–2491` 直接注册 mercenary read-only tool；`native_driver.py:9021–9027` 沿 `query-player-mercenary-context-v1`，既有条件为 paused snapshot、fresh expected_revision 和 advertised `game.command.query-player-mercenary-context-v1`。定向源码确认不用新增 mercenary 专用 CLI，成熟19 opts 原样；MERC 名称过滤为空不代表 OFF 或无端口。

Commander sole：3 个 scoped raised armies，共104 ArRg；type_read_fail0，36 tier0 / 1 个 positive tier2 / 67 type_absent。type_absent 为合法 null，不作读取失败。

| scope | rows / strength | tier0 | type_absent | positive tier |
| --- | --- | --- | --- | --- |
| main301989997 | 39 / 3178/3874 | 13 | 26 | 0 |
| guard184549452 | 24 / 3000/3000 | 18 | 6 | 0 |
| enemy268435597 | 41 / 2759/4702 | 5 | 35 | 1 |

唯一 positive 为敌方 mangonel ArRg167772930，20/20、tier2；不能计入我方 K。raised composition 为 production-live primitive；all-owned/unraised 仍 research，不宣称全军完整覆盖或招募权限完成。

WarAlliedSupport sole：mercenary company554，554 全部 composition available=true；CanHire/terms 已观察30项，不推全部 CanHire=true。positive-tier current companies0，已确认 production-live primitive 的 zero-positive-tier 分支；无 hiring 声明。

NativeTick sole：P470 当前 M60900 / K0 / D93732，fresh L18d，cold stored prepared0，counter12；disease1/desertion1/breach0。B3178、fort6、G550，work4847152/55m（8.813%）、CanAssault=false。这些是同日读回字段，不补写未给状态、未来事件或推进日。

Native22 / registered MCP21 GREEN 原 fixture 复用；new-PID domain qualification 来自本次真实 MAIN。fixture、primitive 与完整 OODA 分开，未重验或重编。

## 外置执行与回执入口

`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v67/packet-official/PACKET-OFFICIAL-DELIVERY.json`：已绑定 fill / renderer / prepare / verify / stage argv，renderer 输出 `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v67/v67-root-packet`。Root 顺序为 SDK 正常关闭与 old-run normalstop → fill → 首次 renderer → prepare → verify → stage10 → retire/rebind/preflight/allocate/start/cold → 三次 MAIN；所有相依步骤等待前步结束。

`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v67/packet-official/MERCENARY-PORT-BINDING-RECEIPT.json` 记录唯一 targeted source read 的静态注册条件；`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v67/rebind-cold/REBIND-COLD-DELIVERY.json` 归 C lane。后续实际 env/PID/SAVE/三条返回只由 Root 与各 sole consumer 给出；本投影未读 SDK/raw/State，未执行 helper、SDK、build、Git 或窗口操作。

v66 正式 handoff38815705 的历史截点保留，本稿不改写。
