# R0171：县域扣兵当前输入的真实暂停帧验收

2026-10-05，CK3 exact 1.20.0.3。源码为 `7f1db1a773e647b9f31378d4a9ccf57a60cf9e73`，a08 DLL 的 SHA-256 为 `8d4d80249ccdfed0954181df38d81daec9740f809fe59dc6c3e7b6708872cc28`。R0171 新会话实际返回了 `county_entry_inputs_v1`：无路线时预算可用、条件未知；写入真实路线后，条件以路线首省求值。这里只闭合当前输入的运行时观测。

机制与 ABI 见[原生当前输入专题](army-county-entry-current-inputs-12003.md)。本次[便携索引](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0171-county-inputs/index.json)、[摘要](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0171-county-inputs/summary.json)和[完整原 JSON](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0171-county-inputs/raw/)保留精确字节及 SHA；复验只读本包，不需要游戏、SDK、媒体、Windows 或原机器路径。

## 两份实际观测

调用的是已有 MCP `ck3_query_army_strengths`，对应生产 step `query-army-strengths-v1`。两次真实参数分别为 `army_ids=[0], expected_revision=3` 和 `army_ids=[0], expected_revision=4`，没有新增动作接口。SDK 原响应、请求原字节和 Root 提取的完整 body 均已保存并互相核对。

| 字段 | 原路线为空 | 移动命令之后 |
| --- | --- | --- |
| 查询帧 | native:2 / public revision 3 | native:3 / public revision 4 |
| date_raw / paused | 53147376 / true | 53147376 / true |
| Army FullID / native CArmy FullID | 0 / 0 | 0 / 0 |
| 玩家、军队 owner | 33388 | 33388 |
| 当前省 | 1506 | 1506 |
| 当前/最大兵数；实际团 | 6746/6747；27 | 6746/6747；27 |
| 已读完整存储路线 | [] | [725, 1009, 2174] |
| 当前县域预算 | 236 | 236 |
| effective_fraction_raw / scale | 3500 / 100000 | 3500 / 100000 |
| minimum_multiplier_raw / scale | 70000 / 100000 | 70000 / 100000 |
| loaded_minimum_soldiers | 5 | 5 |
| 条件状态 | unavailable，no_stored_route | available |
| 条件 actor/source/target/mode | 全部 null | 33388 / 1506 / 725 / 1 |
| 条件 passes | null | false |

预算 `236` 来自原生当前 getter；`6746 × 3500 / 100000 = 236.11` 的整数截断与该读数相容，但该算术不是执行证据。路线最终目的地是 2174，条件实际使用首省 725。无路线的 `passes=null` 没有被改写成 `false`。

移动后 `current_movement_progress` 为 available，首边剩余时长 `raw=3000000, scale=100000`，即当前 30 天；首边进度 `raw=0, scale=100000`。当前省仍为 1506，两帧游戏日期差为零，因此没有到达窗口。当前 `passes=false` 只描述本帧条件，不承诺未来到达时条件仍相同。

## 身份、团与 DATA 完整性

两帧的 episode ID 均为 `native-33388-88a82177b681`；玩家存活、身份 ready。Army owner、FullID、当前省、可控状态相同，端点均无 active event/pending interaction、无战斗或退却。`native_army_resolution_v1` 为 resolved/ready，entry FullID 为 0。

27 个 actual `regiment_strengths` 的 FullID、current/max、兵种与 composition 字段逐行完全相等，总和为 6746/6747。27 个 `regiment_replenishment_records_v1` 容器全部 available/ready，逐容器 count 与实际列表长度相等，共 37 条 DATA，完整数组也逐行相等。FullID 56–60 的五团各有 1/1 兵、DATA count 为 0：没有 DATA 记录不能解释成没有实际士兵。`army_update_clock_v1` 全 block 两帧相等。

这些是同一游戏日期的当前状态比较，兵数差为 0；不提供扣兵/补员事件账本，也不将某一帧的补员条件外推到未来月份。当前 `loss_application_inputs_v1` 还给出 supply budget 0、siege budget 67、raid budget 0，它们同样只是当前预算。

## 版本与部署来源

本次 exact EXE 的归档 SHA-256 为 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。完整 a08 构建回执绑定 exact 源码、Release/16 jobs、三目标及二进制哈希。原始 `native_session_ready` 完整记录显示最终会话 PID 19092、final_bridge 使用该 a08 DLL/injector 路径并实际声明注入；SDK-ready 的 pipe 与该会话一致，实际加载的 `army_county_entry_inputs_contract` 来自 `C:/w/e4countybuilda01/ck3_autonomous_player/src/`。

Strength 的 `source.game_version` 和 `source.executable_sha256` 实际为 null。本包使用归档 exact build、源码/构建回执、会话实际路径和 SDK 模块来源进行绑定，不伪称这两个字段由查询包自带。会话日志仍在追加，本包只取第二行的完整原始 ready JSON 记录，未把它包装成完整会话日志。

## 完成与剩余边界

本次完成了 a08 当前预算和实际存储路线首省条件的运行时验收，新的匹配 Python normalizer 在真实 SDK 中被加载。离线验证器只检查这些精确文件、帧 join 和观测值，不生成新实机结果。

仍未闭合 actual applied-loss/refill ledger、executor 特殊 R9 布尔入参、逐团 loss eligibility、真实到达后的整数损失及 William 饥饿阈值跨越。`loaded_minimum_soldiers=5` 是县域最小兵数输入，不能当成已经读到行军锁定天数阈值。当前预算 236 不等于已扣 236，更不等于 236 人死亡。本包没有新的到达、损兵、饥饿镜头完成或成片签核信用；旧 R0162/R39 证据不补记为 R0171 发生的事件。

从仓库根运行：

```text
python promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0171-county-inputs/verify_package.py
```

在其他机器可把整个证据目录原样复制后运行同目录 `verify_package.py`。原响应内的历史绝对路径保留为原字节；复验读取的全部依赖使用包内相对路径。
