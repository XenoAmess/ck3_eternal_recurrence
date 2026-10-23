# R22：curse 代表场与保留库存证据审计复验

`machine_id: pc-20260924rtuf-f11af23c08`。本稿记录时间为 2026-10-23 UTC；外部证据根目录以下记作 `EXT = D:/workspace/ck3-living-artifacts-20261022`。

R0022 已完成代表场验收：17 自然日、160 public calls、7 Saves，五项检查全部 PASS，`original_action_unknown=false`。Root 正常 GUI 退出、OS/native 零退出及 CAS 释放后，原公共 verify 也实际退出 0，case contract、GUI contract、normal close、case acceptance 与 qualified boundary 均为 true。host 原 wait 1 和原生报告 RED 保留；`business_pass`、`product_release_pass` 仍为 false，未外推整个产品或未测矩阵。

## 本场来源与修复边界

- 冻结候选：`EXT/runtime/c22`，detached HEAD `51b4cc00d4e98e39e2b932a1d5b7900f27e5b016`；唯一 parent 为 c21 `d32238154123bd0c9476577fcd6bf8f5762e2b7d`。
- 仅采用 `EXT/environment/r20-native-audit-fix-a01/c21-successor-patch-a02/manifest.json` 的十个目标：四份既有生产消费者、三个既有测试模块及三个小型 R20 原始行/回调/来源 fixture。该 manifest 为 16801 B，SHA-256 `16415885b1b86c7032febe22515f78078c539c25090f12016897de3c4756bbdd`。
- threshold 保留 c21 的 v1 result、`run_case` 和 `verify_case` 合同，只引入这次库存审计函数、导入与 evaluate 消费改动。其余三个生产目标与已资格主线审计修复逐字节相同。host、SDK、native、MCP 请求、catalog、业务合同及正式产品文件均保持 c21 来源。
- a01 的生产 patch 未采用；a02 引用其中三份不可变原始 fixture 附件。provenance JSON 经正常 Git 流程由 CRLF 变成 LF 的补注及旧 Pin 均保留。

R20 的原失败来自最终消费者把一个有明确来源的 `original_open_intent_not_admitted` 库存 OPEN 拒绝行，当作必须成功的普通原生行解析。修复只在完整重验原拒绝、canonical 前后 ITEM、Root reviewer/回调、映射与图片 Pin、同暂停场景和真实库存可见后态后，将该行分类为未成功提交的 OPEN。真实装备仍须后续原生 EQUIP 与保存状态证明；其他失败、UNKNOWN、错来源或不完整 GUI 证据继续拒绝。

原 R20 的 17 日、160 calls、7 Saves、五项 FAIL 及 `normal_close_qualified=false` 原件保持。修后纯消费者对保留七份证据的五项一致性 PASS 不改写该场实机验收结果。

## c22 实际离线资格

唯一原工具 session `78286` 实际退出 0，terminal chunk `d3753d`。每条命令的原 Popen、wait、超时与日志保留在 `EXT/environment/c22-offline-a33-preparation-a01/`。源码停写后顺序执行六条命令，前置非零即停止；本次六条均实际为 0：

| 命令范围 | 实际结果 |
| --- | --- |
| 完整产品 `unittest discover` | 229 tests，166.623 s，OK；Popen 1840，10:38:27.730473Z 完成 |
| cold workflow 六个模块严格检查 | 6 source files，无诊断 |
| 独立 profile inventory | 8 tests，OK |
| 独立 vanilla saved-campaign | 8 tests，OK |
| 完整产品 `mod_living_artifacts/tools/` 严格检查 | 53 source files，无诊断 |
| 三个修改测试模块严格检查 | 3 source files，无诊断 |

前四条完整消费现行 `living-artifacts-cold-persistence.yml` 对应 step；独立 vanilla 八项不代表 SDK continuation。此包未改 SDK 持久化、cold/warm 序列化或请求合同，未重复公共 step110/E02 或新 C++ 构建。229 的计数对应这一份隔离候选。

正常 freezer 原 Popen 3660 实际退出 0，使用 `--normal-successor`、既有 c18 203 registration 原证据和 cold-profile-v2 host-change 原证据。正式 build 原 Popen 876 实际退出 0；生成的 **57 文件全部与 c21 正式 stage 逐文件尺寸及 SHA-256 相同**。全量读回 11010 个 frozen source Pin 合格且与 c21 同字节；5473 个 native source Pin 也与 c21 相同。

公共 plan → prepare → preflight 的三个原 wait 均为 0，operation 分别为 `20261023T104106399729Z-plan`、`20261023T104112460868Z-prepare`、`20261023T104118576471Z-preflight`。原离线 a33 config 不含猜测的 `previous_*` 或 run ID。

| 固定输入 | 尺寸 / SHA-256 |
| --- | --- |
| `runtime/runtime.51b4cc00d.json` | 2658 B / `601ce814a1f9bfa00ad3a4c28a4b4f6c09346ca187fbffefcbf0d2737f38963b` |
| `runtime/next-public-operation-a33.json` | 961 B / `220e3817d7a7abf5005e599859c520edb435044e01f55cdded6803d1fdaa74ef` |
| `runtime/prepared/living-curse-a33/prepared-case.json` | 34811 B / `252f142acced096326644500c90bdc712286bc58a264451eada63e7b144d4167` |
| `runtime/c22/mod_living_artifacts/tools/checkpoint_producer.py` | 30478 B / `4ed0dd6195d592ceb72159b33f40fc6f37d82d51cffd53887b03635e47243261` |

完整 Pin 表与实际资格边界见 `final-source-qualification.json`（4256 B，SHA-256 `63ee42dd9cfbb6303902bfe3a2b9df94c89a90ac67bb430e080fdee3afd136f2`）。正式 57 文件清单见同目录 `formal57-comparison.json`。本场合同保持 17 自然日、最多 7 Saves、420 public calls，以及原五项业务断言。

## Root 实际启动

Root 绑定 R21 的正常 release（857）并消费 bound preflight 0 后，由原 allocate session `63425` 分配 `pc-20260924rtuf-f11af23c08--living-artifacts--R0022`。keeper PID 13988，lease CAS 862；随后原 run session `90738` 启动（最终 wait 0 见闭场节）。Root 为唯一游戏、GUI、七保存回读与退场操作者。

10:47:07.338111Z 的新鲜后台 Steam 回执为 `status=offline`、`offline_mode=true`；2332 B，SHA-256 `6c5dc4a336ea2515a8fa31dbfd7951fc8a5b00f1014e3e3f55a573099e0941a6`。host 于 10:47:15.007104Z 启动，PID 2096；Root 记录 CK3 PID 8880、birth `1792752444.316454`。host 的已准入冻结 argv 保持 readiness 1800 s、hold 5400 s、timeout 6600 s。

稳定小来源均在 `EXT/live/pc-20260924rtuf-f11af23c08--living-artifacts--R0022/`：

- `run-context-r22-20261023-a01.json`、`allocated-context.json`、`ready-context.json`；
- `host-started.json`（3620 B，SHA-256 `7da6ce8cf61f8e002c3417a7179efd0416cbbd0f8948f23ceec925c299341f09`）；
- `keeper-process.json`、`frozen-argv.json`（71125 B，SHA-256 `dd6ffcf3f45d17f0acbacee02a482079c8059e55a621ce95a9061c62028e091e`）；
- `steam-offline-r22-20261023-a01.json`。

## 已确认的真实保存

只读 `curse-checkpoint-01.json` 及其绑定的小型 process 回执确认：首 Save 的原 melter Popen 8200 实际退出 0，10:54:51.821091Z 完成。投影绑定 CK3 PID 8880、generation `1`、actor 31254、date raw `53144328`（1066.9.15），目标血咒物品 402；贵族胃与候选分别为 403、404，三者此时均未装备。

保存与独立同暂停原生钱包均为 Q100000 `2000000`（20 金），prestige `220000000`、stress 15 一致；初始 native health 为 Q100000 `466160`。首份保存的初始钱包与声明输入相符，尚不能授予装备、月付或完整五项业务信用。

`curse-checkpoint-01.json` 为 19276 B，SHA-256 `c8c255a7c92117ef531208aafe35be3ac0f84c29684c5ab8219bce2b0161077e`。其原始保存 Pin 为 70636928 B / `47adc6c221ddf8f9506570726dd6cdabfaa4976a70da4841c5df57e97397955f`，process 回执为 3043 B / `7010a2c608b293f0c6bdaa799a8fb1835ce731d3a5956001595eb8047e51035f`；本报告没有重新读取或解析大 Save/melt。

Root 的首两次手工 readback 原工具分别为 60303、70532，均实际 wait 0；保留 melt 尺寸为 103709331 B、103709933 B。收到第二次 producer 终态时，typed projection 尚未落盘；随后实际读回 `curse-checkpoint-02.json`（19275 B，SHA-256 `9f2c7c8179d1428d357276b37d2feaba6af5ed106b8ac57a8d7819e7a1ceda68`）：同 actor、同日、同 date raw 下，402 已装备，saved/native 钱包仍为 Q2000000、stress 15，native health 为 Q346160，较首份减少 Q120000。403、404 仍未装备。

第三次 readback 由 Root 原工具 chunk `7175d1` 实际返回 0，melt 103709897 B；随后 `curse-checkpoint-03.json` 已实际落盘（19276 B，SHA-256 `53f1ee9cb8ad6ee2a63ac7351aa87fcc3891d7aa7589c5cf118872da69e3d480`）。同暂停日期下，402 已卸装，native health 回到 Q466160；保存与原生钱包仍为 Q2000000、stress 15，403、404 未装备，候选 404 仍为普通未判定输入。血器的实际健康序列为 Q466160 → Q346160 → Q466160。本报告分别记录 producer 与实际消费阶段，不重复调用 producer。

第四次 readback 由 Root 单次完成，原工具 chunk `99d037` 实际返回 0，melt 102802587 B；`curse-checkpoint-04.json` 已读回（19046 B，SHA-256 `be085a979362e7cd93a0a126936b4ba62c4b1af57dfa738fc9dbff5e132f74e1`）。场景为第 15 自然日、1066.9.30 月底结算之前，402 未装备、403 已装备、404 未装备且仍普通未判定；saved/native 钱包均 Q2000000、stress 15。此 checkpoint 未安排 health 查询，投影明确为 UNAVAILABLE，没有补造数值。

第五次月付后 readback 位于第 16 日，Root 原 session 22450 实际 wait 0（chunk `bc29cc`），melt 103489514 B。随后实际读回 `curse-checkpoint-05.json`（20682 B，SHA-256 `3af6d6b64c8fdb9975a3414dd3eb4cb0b8a8d9c01a0608e26fadb15b6dafb46f`）：1066.10.1，403 仍装备；saved/native 钱包均为 Q0，stress 均为 45，相对 CP04 实际支付 Q2000000（20 金）、压力增加 30。403 的 `xalw_last_settled_month` 已为 12802，level 1、XP 8；404 此时仍为普通未判定物品。本场这些数值来自 R22 自身新投影。

本场没有其他 producer 或自动 checkpoint service，未把不存在的 service 进程记作成功退出。

第六份保存由 Root 在同日重复装备操作后单次完成，原工具 chunk `5ae850` 实际返回 0，melt 103489649 B。随后 `curse-checkpoint-06.json` 已实际落盘（20833 B，SHA-256 `2e70882867210f622c758c54f8b65ef0fe31804889961161096ab47501d865fe`）：仍为 1066.10.1，403 已装备，saved/native 钱包均 Q0、stress 45；与第五份相比未再次扣款或增压，403 的 last month、XP 8 和候选 404 的普通状态保持。

第七份由 Root 原 session 66455 实际 wait 0（chunk `49138f`），melt 104010836 B。七个原 producer 此时均已返回 0，无在途 producer、无自动 service。`curse-checkpoint-07.json` 随后实际落盘（20843 B，SHA-256 `562cb1d4c37ecde675d95ed1f79f23d5e3b5a48ae2149eb17247636dc9b47230`）：1066.10.2、第 17 自然日，saved/native 钱包均 Q399603（3.99603 金），prestige Q220196910，stress 45；相较 CP06 的次日钱包增量为 Q399603，未沿用其他场次收入。403 仍装备、last month 12802、level 1/XP 8 保持；404 仍 ordinary、未装备。候选样本记录真实普通状态的持久一致，不授初次发现/觉醒见证或新词条信用。

## 实际库存回退与独立装备后态

`xalw-core-0006.actual-results.json` 是本场原生 OPEN 的既有预意图拒绝，675 B，SHA-256 `12985923b1b1144e84c4086d7a30aab7ef731db420dd4bcdd6ac6a0a2a7ec3c1`。Root 首次 fresh-control pixel 比较拒绝且未发输入；原失败保留。Root 随后直接审阅新原图，经 canonical mapping 单次点击 `(386,996)`，实际图龄 28.246 s、HWND 8586208。

Root 回调 `inventory-gui-open-0006-root-result.json` 为 1447 B，SHA-256 `52c3d2b9836a2ce758a42029ee3823cad91c951fee87aed7547480ee5c48a5df`，绑定本场 PID/generation/actor/date、目标 402、原拒绝、mapping 与前后图。独立 native ITEM0007 读回仍未装备；实际装备经 native EQUIP0009 只提交一次，其返回为 `original_callback_invoked_post_pending`，随后 action-post0010 为 `desired_inventory_state_observed`、`needs_recovery=false`。

| 原生来源 | 尺寸 / SHA-256 |
| --- | --- |
| ITEM0007 | 25813 B / `015f7ca8c49614e4018b5eee361b2e39f6536e2f016f8fdd5830134468a1e52f` |
| EQUIP0009 | 27710 B / `7577934a28dd4d407cee154ae6a7335f4d154d128c9928e2f75ee0e6c5a9c2a9` |
| action-post0010 | 33434 B / `4042cc5da01c2f37443503bd05ff8d15040a502c9a1c04c50cd3ec211936a7c8` |

Root 另直接审阅延迟原图 `media/20261023T110418835618Z-r22-inventory-actual-after-a01.png`，2468956 B，SHA-256 `095b3ca64ee3e1e9230ae219045b6e66a793bf8b3fdb3e51a9d39f6466257421`；记录可见七件、两件星名及 20 金。该图摄于 adapter 已开始装备之后，空 slot 的渲染不作装备状态证据。`environment/r22-inventory-root-review-a01.json` 为 1116 B，SHA-256 `ba8e5b276760fe11558aa0deb242b9522ed84fa1d95dc71a263e9737aec9ad2f`，明确装备信用只来自原生后态。

## 五项实际结果与闭场边界

原结果为 `case-output/living-artifacts-curse-representative-result.json`，1288014 B，SHA-256 `317a0fb3283481dbe4a839c8c72af3d741d8fac4e159fb8c356f99891af4dea8`，实际观察时间 `2026-10-23T12:02:52.155960Z`。原 evaluate 重验七份 checkpoint 和九个库存 GUI 证据 Pin 后得到以下 `fixture_live` 结果：

| 本场检查 | 当前记账状态 |
| --- | --- |
| CURSE-BLOOD-EQUIP-REMOVE | PASS |
| CURSE-APPETITE-BOUNDED-PAYMENT | PASS |
| CURSE-SAME-DATE-NO-RECHARGE | PASS |
| CURSE-NEXT-DAY-NO-RECHARGE | PASS |
| CURSE-CANDIDATE-PERSISTED-JUDGEMENT | PASS |

结果实际为 17 自然日 / 408 小时、160 public calls、7 saved observations，`original_action_unknown=false`、`error=null`、`case_contract_qualified=true`、`gui_contract_qualified=true`。实际 quote 50 金，支付 20 金、短缺压力增量 30；次日钱包变动 Q399603、压力变动 0。候选 404 的持久化判定为 schema 2 / ordinary / 空 roll fields，`candidate_first_unjudged_observation_credit=false`。

原结果写入时为 `normal_close_pending=true`，正常闭场归共享 entry/CaseClient；`business_pass=false`、`product_release_pass=false`。下节的独立正常闭场、CAS 和实际公共 verify 补闭合后续阶段，未改写这份原结果。本场不授 NPC、战斗、双物品叠加、cold、suppression 或整个产品发布的额外信用。报告只读既有投影/小原生结果，不重复解析 Save 或提交动作。

## 正常闭场与公共 verify

Root 直接审阅原屏中未勾选的 autosave checkbox，12:20:56Z 单次点击正常 Quit to Desktop。原 CK3 于 `12:21:07.786150Z` 实际 `process_exit`、exit code 0；保留 OS handle 读回 0，native shutdown cleanup=true，最终 CK3 inventory 为空。共享 close 为 `normal_close_qualified=true`、`failure_preserved=false`、`host_error=null`。

host 原 wait 为 **1**：原 OPEN 拒绝行令原生报告保留 RED，该行和 host 退出码均未改写。它由当前有来源的库存审计分类并重验，不能据此把整个 host 报成 GREEN。原公共 run session 90738 实际 wait 0，原 allocate session 63425 / keeper 实际 wait 0。

| 闭场证据 | 尺寸 / SHA-256 |
| --- | --- |
| `case-output/normal-quit-root-result.json` | 1813 B / `7051c5d98af03b4767a799b8cbde9651382d846d826919d063f405c017c52523` |
| `case-output/normal-close-result.json` | 8786 B / `ff2004ba2d52e8213276d5aa09325944b0067f1dbd468edb4cb4016783bcdd5b` |
| `environment/r22-normal-screen-resource-close-a01/release.stdout.json` | 1286 B / `7b387400240d0bb13f72167ba19cf3dd22a82ceb686ea445cf63c6a0cc0e3872` |

CAS 898 于 `12:21:59.091127Z` 将 a33 task 置为 done、resources=[]。此处仅记已实际完成的本场资源释放，不授新场或发布权限。

Root 通过原 c22 公共入口、原 runtime/products/Prepared 和真实 `run-context-r22-20261023-a01.json` 执行 verify：operation `20261023T122159379063Z-verify`，原工具 session 81272 实际 wait 0（chunk `3936b1`）。原 Popen 11128 在 `12:28:16.226563Z` 实际返回 0；Root 于 12:28:34Z 确认外层原工具终态。

`exit.json` 为 185 B，SHA-256 `8e66f4e925a65218717e04ce02c97160c808fff5209c365c9c26a549093e7e49`；公共 `stdout.json` 为 1325702 B，SHA-256 `452aec9ece6afa2f2fb1dd99166e08c318ee77076746f5c22715a8da8b670eee`。实际为 `status=PASS`、`error=null`、五项 PASS，case contract / GUI contract / normal close / case acceptance / qualified boundary 全部 true；business 与 product release 两项 false。原 case 结果仍精确为 1288014 B / `317a0fb3283481dbe4a839c8c72af3d741d8fac4e159fb8c356f99891af4dea8`。

只读核对 c22 公共源码：`Selection.verify`（853–870 行）先在真实 SDK import scope 中调用冻结 adapter；curse `verify_case`（540 行）实际重算 evaluate，后者调用本次 source-bound `audit_native_records`。公共入口以 case contract、GUI contract 和独立 normal close 三项计算资格，未要求把原 host 1/report RED 改成成功；精确原拒绝必须通过全部 GUI 来源守卫，其他失败/UNKNOWN 仍拒。本次实际七份证据复验与 CLI 原 wait 已证明这条边界接受本场有完整来源的 OPEN 拒绝。

## 存储与文档范围

c22 离线包沿已采用的 `storage-curse-a33-20261023-a01` own 3 GiB 内的 offline 512 MiB 执行。最终静态 **392690606 B**，已补计 build 同时生成的 ZIP 643724 B；原遗漏点量保留，并在新 closure 明示。独立观察到已启动游戏的 profile 增长 19371441 B，单列为运行期分量。采样不声称连续峰值证明。

离线 child 的 fresh task-close 原 wait 0 已消费，小包最终 137 files / 220601 B、tmp 0、future-write 0；`child-closure.json` 为 1488 B，SHA-256 `f38da347f02555f50a6b47a7d6c35c79b021d5269b47a7009cc620f2e57f9b76`。此关闭不释放 Root 的父 own 或 other 预算。

本报告单独计入 a33 other 128 MiB 中的 ≤2 MiB 文档子范围，fresh task-start `20261023T105626416387Z` 和 before-heavy-write `20261023T105628223903Z` 均实际退出 0，四张父卡未变。完整结果与公共 verify 已实际收口，报告正文停止编辑；文档 child 的最终 storage-close 另行消费，不释放父预算。
