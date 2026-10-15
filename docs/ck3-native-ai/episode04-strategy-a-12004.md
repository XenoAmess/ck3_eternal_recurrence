# 第4期 R10 A 臂：整军直达的决策输入与逐日状态

本页及[独立消费者](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_a.py)补足 A 臂的可执行输入，不修改公用比较器、原生接口或生产 DLL。适用合同为 [R10 同起点比较](episode04-comparison-contract-12004.md)。当前状态为 **offline consumer tested**；新普通存档 T0、目标、Army、统帅、cohort、实际首次抵达和费用均未在此工作包取得，保持 `null`。UNBOUND 模板不能直接执行，不能用测试 ID 或旧罗贝尔路线填空。

源码阅读基线为 `1463bd9b4b89612d283dd45ac4ec9efbf22f048d`。工作包在 `machine_id: desktop-3fevhd2-1c74096080` 于 2026-10-15 独立离线完成；准确观察时间、解释器、命令和结果见[测试回执](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/validation/strategy-a.actual.json)。这个机器标签只绑定本次文件消费和测试，不重授游戏安装、Steam 离线、生产 DLL 或实机资格。

## 可直接调用的四步

`strategy_a.py` 复用邻目录 `r10_compare.Evidence`、`endpoint`、`frame`、`clock_days` 和现有 schema。它不调用 SDK，不读取存档、游戏二进制或媒体；Evidence 只读指定 evidence-root 下的精确小文本 pin。状态返回新副本；异常不更新原状态。

```python
from r10_compare import Evidence
from strategy_a import admit, observe_move, update, report

evidence = Evidence(small_evidence_root)
state = admit(plan, runtime, loaded_save_sha256, cold_start,
              fresh_preview_pin, evidence)
# 执行者在当前冻结帧按 state['proposed_call'] 调用已有 ck3_move_army。
# 这里只生成建议，没有发命令；结果未知时不重发。
state = observe_move(state, independent_after_endpoint, evidence)
# 后续每个实际自然日调用一次，不能以脚本重启重新从第1日计数。
state = update(state, exact_day_clock_row, full_same_frame_endpoint, evidence)
a_report = report(state)
```

`admit` 只校验 A 所需的冻结条件，不要求 B/C 先取得资格。R07/R08 未闭合也不阻止基于当前状态的合法行军；`actual_fees` 在此消费者始终为 `null`。完整 ABC 的计划准入、策略遵循、事件记录与费用账仍经既有 `r10_compare`。不得把本函数返回解释为完整比较已合格。

冻结 preview 绑定初始 baseline 的 episode/frame；独立冷载后的 fresh preview 绑定本臂自己的 episode/frame，两份不能互相冒充。两者分别验证完整路径、Army、真实起点、目标和时间；冷载路线与冻结直达路线不同时回到冻结条件核对，不静默改计划。`admit` 验证 `.4 / Steam25734779 / EXE98702f88…9518`、source/DLL、正常 checkpoint pin、T0 观测等价和源会话身份；hash 与声明一致性仍不证明来源真实性，执行者保留独立运行 manifest。

A 初始策略 Army 必须是一支整军，完整 scale1 ArRg ID 集合覆盖所有初始团；public CUnit ID `0` 有效，不能混用 internal CArmy ID。每日显式 query scope 必须仍为这支整军，DATA 覆盖、人数整数及求和、原队列和逐军库存/cap 均完整。新自然生成记录继续出现在 `all_strategy_*`，原 cohort 单列；缺团、unknown 或 shadow 不补零。分军/合军发生后不能继续把该记录叫 A 的整军不变策略。这个有限消费者不尝试解释被销毁队列的原因。

`observe_move` 接受同日、更新 native revision 的独立暂停后态，实际 target 和完整 route 必须匹配 fresh preview；它不接收 Move ACK。随后 `update` 仅接受连续第1至90日：复用已有 exact sentinel 的 generation、实际 start/target/end、speed5、tick1、零越步和暂停来源，并核同一 snapshot pin/Army scope 的完整结果。停军、接敌等当前状态中断保留为 `needs_current_state_decision`，交现有完整规划器处理；本模块不重发 Move、不把接敌删成测量噪声，也不产生战争胜利。

首次抵达要求真实 current=冻结目标、冻结允许状态、完整空 route 和 target=null。保存 `(最后未到日, 首次已到日]`，宽度一日；ETA、路线长度和 ACK 不授抵达。`arrival_actual` 在首次到场冻结，后续读数仅进入 `current_actual`；`report_date_endpoints` 只含预注册自然日的本臂真实 endpoint，`joint_common_date_rows=null`，直到公用比较器取得三臂同日值。D90 endpoint 还需预先冻结到达后政策和实际90日读数。真正未到且取得90个合格日才标 `budget-censored`；第38日停止不能当90日截尾。死亡、原队列无法绑定等竞争/测量终点由执行者保存其原始证据及独立 disposition，不伪造一个可读的存活完整终点给本函数。

## 当前缺值与最小现有查询顺序

| 当前字段 | 本包值 | 由现场执行者取得的现有输入 |
| --- | --- | --- |
| 正常同 T0 checkpoint bytes/SHA、save receipt、来源证明 | `null` | 既有正常 checkpoint 及独立 manifest；不读取或改写大存档内容 |
| 当前 actor、episode、PID/create-time/generation、revision、Army 与所属 | `null` | `ck3_take_snapshot(include_native_command_history=false)` 和该会话运行 manifest |
| 共同目标 Province ID 及战争目的依据 | `null` | 从该帧现有 war objectives / occupation target 行冻结；未发布目标先复用 `ck3_query_war_occupation_targets_v1(war_id=当前war, expected_revision=本帧公开revision)`，不以地图相机中心或旧伦敦路线代填 |
| 整军全体 ArRg current/max/DATA、库存/cap | `null` | `ck3_query_army_strengths(army_ids=[本帧public CUnit], expected_revision=本帧公开revision)`，取完整 Driver JSON |
| 统帅与 loaded features 精确来源 | `null` | 同帧 `ck3_query_army_commander_candidates_v1(army_id=本帧public CUnit, expected_revision=本帧公开revision)` 与 hello/manifest；用 endpoint 的 bound source + JSON pointer 指向真实字段 |
| 直达合法路径 | `null` | `ck3_execute_step(step="preview-move-army-<public CUnit>-to-<共同目标>", expected_revision=本帧公开revision)`；完整回执，不存在名为 `ck3_preview_move_army` 的入口 |
| 提交与实际首次到场 | `null` | 已有 `ck3_move_army`；独立暂停后态；逐日 exact sentinel + snapshot + 完整 strength query |

顺序为：先 normal T0 与 snapshot/manifest，确定真实 Army 与共同目标，再取完整 strength/统帅和合法 preview，冻结计划；A/B/C 各自独立冷载同一 SHA 后重读相同观测，A 再取自己的 fresh preview。任何查询越帧即更新 snapshot 后按该新帧重取相关输入。未先取得 Army 或目标时只缺这些具名输入，不新增选点平台。公共目标的玩家策略依据由 R10 执行者冻结；仅有合法 preview 不意味着它军事上最优。

ETA 为可选解释，不是 A 执行必要字段。需要时复用已有 route-contact literal 及当前完整 hostile 集合；h-N 是敌军数量，一日 contact 范围不外推为全程无敌。一般 preview 没有 ETA 时保持 `null`，不用 hop 数计算；独立首次抵达仍按每日实测。

## 源码依据与验证边界

| 链 | 阅读位置 | 本模块使用方式 |
| --- | --- | --- |
| `.4` adapter 复用 PreviewMoveArmy | `ck3_autonomous_player/native_bridge/src/ck3_12002_adapter.cpp:313` | `.4` descriptor 显式走既有 preview，并补原生省份补给输入 |
| 实际军队/目标解析与合法性 | `ck3_autonomous_player/native_bridge/src/ck3_12002_military.cpp:353` | 原生 paused、FindControllable、province resolve、move-mode、character/Army command guards，继而 build_route 并核末端目标；不自造许可 bool |
| native available 才发布 | `ck3_autonomous_player/native_bridge/src/bridge.cpp:29303` | deferred/拒绝不变成可行动 preview |
| Driver 固定同帧来源 | `ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py:14400` | `queried_snapshot_id/revision/native_revision/generation/episode` 与 `previewed_date_raw` 完整配对 |
| 完整 cohort/DATA 与每日自然钟 | `promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/r10_compare.py:96` 和 `:156` | 复用现有读取器，A 额外要求显式 scope 与 route 状态自洽 |

运行 `python -B -m unittest discover -s promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison -p test_strategy_a.py`。测试仅在临时目录生成明确 synthetic native 形状数据：跨帧/episode/generation、正常存档与 source 绑定、未知 scope/DATA、原团丢失、ACK、实际后态、一日首次抵达、原 cohort/新增团分列、零越步、连续90日、早停与到达后分表均有实质检查。它不构造存档或 fixture gameplay。`open_kaishek` 为 `not-applicable`：本包只消费已导出的 JSON/原生回执，不运行 CK3 script/parser/IR 语义。

旧 R0173 的来源机器与本次文件消费机器 ID 相同仍不等于同一进程或新 T0；其登船3金币和未锁 Halt 仅保留[原有实证](episode04-r0173-boarding-halt-12004.md)。旧 B 的+38 gate-stop、C 的 `(75,77]` 和15次偏差继续按公用比较合同拒绝，不回填当前准入。没有新增游戏日、实机研究卡完成、录像 clean span、影片或人工签核信用。
