# A20 已保存进度与闭场记录（2026-10-21）

A20 完成13个 FULL、390个已结算普通周期，实际新增并保存193个游戏日。累计为 **5622／10950日、5143周期**，最终 SAVE11372 与 Driver checkpoint 绑定经小型回执确认，NEXT 为11373。30年目标尚未完成；G2仍为6／8，1秒／日目标未达。

- `machine_id: xenoamess-full-tower-eb9d2c1186`。
- 本文补录：**2026-10-21T06:18:35.578973+00:00**（Asia/Shanghai：2026-10-21T14:18:35.578973+08:00）。机器身份另由本轮 `tools/ck3_live_run_id.py machine` 实读确认。
- 闭场索引观察时间：2026-10-21T06:00:25.565204+00:00；最终 review02：05:59:34.677922+00:00。
- 证据等级：本机 production-live 的保存绑定及闭场记录。本文只复核小型 JSON；没有重新读取、复制或哈希 Driver、SAVE、媒体本体，也不新增业务 RPC。
- 本文为事后补录，不改写[旧交接](../handover/2026-10-20-robert-source26-a05-vacation-handoff.md)的历史截点。

## 进度与终点

| 项目 | A20前 | A20闭场后 | 本轮新增 |
|---|---:|---:|---:|
| 已保存游戏日 | 5429 | 5622 | 193 |
| 已结算普通周期 | 4753 | 5143 | 390 |
| 本轮完成 FULL | — | 13 | 13 |

原 T0 仍为 `date_raw=53144328`，当前保存日期为 `53279256`，原终点 `53407128` 不变；目标仍是10950日，剩余5328日。原整场墙钟起点 `2026-10-19T03:26:49.420926Z` 保持，不因冷启动、维护、录制或本次补录重置。

最终原生保存请求为11372，checkpoint 的 `history_index=5894`，它不是5143个 settled cycles 的别名。review02记录的 SAVE 为117736294 B，SHA由完整原生 SAVE 回执提供；本次文档核对没有读取该大文件。

`ROOT-A20-FINAL-SAVE-VERIFIED01.json` 与 review02共同确认最终 SAVE、Driver checkpoint、日期和身份绑定。其限定仍是 **saved binding verified，未证明 fsync 或断电持久性**，不能把返回 saved／replace 成功升级为更强的存储保证。

直接最终 SAVE 没有回填旧 Queue 的 `actual_saved_checkpoint` 缓存；冻结 Queue 已结算周期为5143，但该缓存仍指向较早的11263保存。连续性 ledger 也可能落后最终 FULL。下一次恢复必须以最终11372回执和 review02核定保存边界，再对齐 Queue／ledger；不能把旧缓存当最终保存，也不重放历史 unknown10565。

## 首个 FULL 的性能边界

首批 control10574 在同一实际 producer 的单调时钟中，从提交至回执校验用了 **50.3175879秒**，日期从53274624推进到53275176，即23日：

`50.3175879 ÷ 23 = 2.187721213 秒／游戏日`。

这是真实首批局部吞吐，**不是1秒／日达标**，也不是全部13批或原整场的平均值。原全墙钟继续包含此前已经发生的等待；不能只换起点或扣除维护后宣称整场达标。首批闭合回执保留完整生命周期的 monotonic_ns 起止与 `full_wall_ns=50317587900`。

本次没有重扫计时 JSONL。现有 inspector 的96组上限和 clock 累计时长口径已暴露独立消费者问题：不能把各条 resume 累计 `elapsed_ns` 相加当实际成本。后继通用 consumer 与 speed4／s4 静态工作包仍在处理，本文不记录它们已经交付、部署或获得新 CI 通过事实。

## 闭场结果逐项区分

- SDK 两进程实际退出码 **0／0**，索引记录 SDK normal。
- Game 实际退出码 **1**，发生原 owned Job 强制清理；最终 Job active=0。**Game正常关闭资格未通过**，不能用 SDK 双零覆盖这一事实。
- 录制 worker 实际退出码 **0**，记录为媒体正常闭合。worker小回执当时仍标记原 Task 的 Job tail pending；后续总闭场索引及原 owner 结果确认三个 Task 实际 absent。本文未读取或审看媒体，不授最终影片剪辑／交付信用。
- screen121 以 CAS7972释放，完成 sequence7973，task为 done、resources为空。
- 现场闭场时间早于原人工 review 截止；索引在闭场后补记元数据，不是对过期现场准入续期。

## G2：本轮没有新增 M6／M7 验收信用

2026-10-21 06:06—06:10 UTC，对冻结四份 sidecar、冷启动前小回执及少量最终 AUTO／MET进行了限定只读核对，没有扫描全部13个 FULL 的业务历史。

| Sidecar | 前置 bytes／SHA256 | 冻结 bytes／SHA256 | 对比 |
|---|---|---|---|
| 01 `faction-gift-pending-v1.json` | 257／`47b63483f700c7c2d0daa55420759c4d6f7f4a7f49cb01273db483f33c522a0c` | 257／`47b63483f700c7c2d0daa55420759c4d6f7f4a7f49cb01273db483f33c522a0c` | 前后完全相同 |
| 02 `active-scheme-sway-formal-private-v1.json` | 21864／`edfd6027bf508bda9ea9183c8820a18014192d20789f6ae929b4e0c503c63580` | 21864／`edfd6027bf508bda9ea9183c8820a18014192d20789f6ae929b4e0c503c63580` | 前后完全相同 |
| 03 `ordinary-sway-schedule-v1.json` | 419／`94a6fa3cb8879392cc5be39670f2085b69eb6a6e72d1213e0976618a9d57ff54` | 419／`94a6fa3cb8879392cc5be39670f2085b69eb6a6e72d1213e0976618a9d57ff54` | 前后完全相同 |
| 04 `first-heir-marriage-formal-v1.json` | 18792／`b9783afadf82d9b1432786a9b7a2718043761ec77e1ecef615e6d469d445eace` | 18793／`761c9f6f700d7ec44fd01cb08cb647bf40fea5c50217441fb0be73dabca028e8` | 仅冷重绑定两身份字段，RAM逆变换匹配旧SHA |

前三份逐 bytes／SHA 与 cold-prelaunch 的前置 pin 相同。M6 的 `last_check_date_raw=53274240`、`next_check_date_raw=53274960`、`last_terminal_action_id=null` 没有变化。旧 action 的最新／terminal 观测仍是 `instance_terminal_outcome_observed=false`、`native_status_key=unobserved`、cause unknown；gain25来自旧日期53225352，不能重复授新信用。独立自然 terminal 与更后的普通消费链仍缺。

第四份婚姻 sidecar 的 SHA变化不是新婚姻结果。只在 RAM 把其 `post_bridge_pid`／`post_bridge_creation_date` 从本轮186516／`20261021052207.763206+000` 逆改为实际 A17 闭场身份83948／`20261020231721.737835+000`，重新编码后精确重现前置18792 B／SHA `b9783afadf82d9b1432786a9b7a2718043761ec77e1ecef615e6d469d445eace`。因此可定位为这两个冷重绑定身份字段的变化；没有读取或伪造旧 sidecar 原件。原 proposal 日期53243808、pre revision2658、post revision2668仍是旧见证，旧 child-house preview174不能升级为新 root-H／广度验收。

最终抽查的 AUTO11369 选择战争 stationary route-contact-horizon 查询，其普通信用回执明确不推断业务成功；MET11370只给出当前 actor40526、日期53279256等指标。末尾 SEM11371没有 `player_heir_fixed_dynasty_projection_v1`。这些有限样本未提供新 M6／M7 正见证；结论保持 **G2=6／8，M7实际 H／广度仍未完成**，不外推为已穷尽本轮全部历史。

此核对未证明有新的 planner 缺失分支；不为凑验收追加 query、强造局面或重放旧 unknown。

独立事件线程另经 Root转述了限定离线检查：12份小index覆盖control10574→11247，首份42个incident均绑定2026-10-19历史PID，当前A20 Game186516为0，后11份也为0；84份before／after小capture与canonical逐bytes／SHA匹配，汇总digest为 `b89ea1e087c52716d0a59befd8293e1e25ceb60a4590fed39d1ace69a4b43d0e`。events72＋interaction12无T之外新增，已有119＋5条registry无需因此新增规则。该证据只覆盖12份index，STOP早于末FULL的离线索引闭合；不能宣称扫尽13个FULL。本文未重复扫描这些capture。

## 精确小型证据入口

以下 `U20` 仅指本机冻结现场根：

`D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime-a20`

表内路径均相对 U20；SHA由补录时实际小文件 bytes 机械生成／对照索引，不是大资产重哈希。

| 小型文件 | bytes | SHA256 |
|---|---:|---|
| `ROOT-A20-ACTUAL-CLOSURE-INDEX01.json` | 11081 | `ef6ecb98d57d20ec00279fd1475ef9de96d061fde9891430b75bda2f45870b86` |
| `ROOT-A20-FINAL-DRIVER-SAVE-REVIEW02.json` | 4626 | `0e94284c1b11c3d2dd29f2ee8941c2378e9a4d6b621a6ab41277456dd62af54b` |
| `ROOT-A20-FINAL-SAVE-VERIFIED01.json` | 2922 | `4ce94fcc987102041e11664fdeae1005487427d58f1a92bf971b0a7a64d5f20b` |
| `ROOT-A20-FIRST-FULL-TRACE-CLOSED01.json` | 2296 | `6a26ffd4a5c760e935e2622412469e576ad0ed7486b1eb64779fbf4dce543185` |
| `ROOT-RECORDING-WORKER-CLOSED-Source28-A15.json` | 756 | `be3f17705d1b5aba3519d476531e1373a517394cf51e6bf03af3277134726493` |
| `ROOT-A20-SCREEN121-RELEASE01.json` | 2170 | `633f1e79740e7c2320edc305fb13be92a8d0f33fc34bbc2b9253ebb95033ee92` |
| `p37-responses/10574-1-result.json` | 2203 | `e2615efa905a23a37d9e9a641dae10a03545f269a009ae7df3d0c95585e6d435` |
| `p37-responses/11369-0-plan.json` | 1978 | `58f20b5220ea99de2619281fe23e2fdd5b54a463477f74985b2f52e465830860` |
| `p37-queue/11369-ordinary-result-credit.json` | 635 | `a712e1a4219d706c7ba4ec1709efe59008532f2bc3b1a0f4e80eb6431c81877e` |
| `p37-responses/11370-1-result.json` | 1812 | `9311cb8c81fd4b5aab92d33cda1cc91477a85f7cfa5363e7e696758594a60265` |

冷启动前 sidecar 的 pin 来源是 U20内 `ROOT-C23-COLD-PRELAUNCH.json`，通过 `ROOT-P37C23-COLD-RESUME-ADMISSION.json` 的精确 ref 绑定。前者10678 B，SHA `8c980ecb3f8e6877e398542e637970e55610525facb944a86530dbeea9d231e7`。旧身份逆变换使用实际 A17 闭场索引的 Game PID／FILETIME，只在 RAM 执行，不新建证据文件。

## Steam 时效与后续入口

A20晚绑定使用的后台离线回执为 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100/source31-a20-prep01/ROOT-STEAM-OFFLINE-A20-PREP03.json`，2480 B／SHA `4a2aef67f0b24e43bdb6759d6da2d8c8526ea63891c9df2c91d32d9ae22a0c12`，观察时间2026-10-21T05:19:20.272254+00:00，`status=offline`、`offline_mode=true`。它仅证明当时本机状态，**当前已不具新启动准入时效**。

下一次受管启动前重新运行后台 probe，取得新鲜且同机器、同 Steam 身份的 offline 回执。查询不得占屏、截图、激活或移动窗口，不因 unavailable 自动切截图，也不自动上线。

下一包应先核准新的人工时效、容量、单一状态 basis 和当前实际文件身份，再由 Root 决定恢复。本文没有启动新 Game／Task、没有修改 U20／SDK，也没有代 Root 提交 Git。通用 basis／speed4静态结果及新的公共 CI 状态须由其各自实际交付另行追加；本文不能代替。

## 文档状态

这两份文档在上述补录时创建，commit／push **pending，由 Root 独占处理**。旧交接、原失败、review01错误字段记录与本轮实际强制关闭事实均保留。
