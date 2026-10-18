# 普通显式认输与自动应急退战

`ck3_surrender_war(war_id, expected_revision=...)` 现在为 CK3 1.20.0.4 提供普通显式认输路径。它适用于已经决定接受投降代价、需要正常结束战争的调用者；原自动规划器仍按既有 `action_steps` 和应急策略生成行动，不会仅因这条接口存在而在普通战局投降。

改动来自信仰一期的实际缺口：R0020 修改主流礼仪时，原版完整许可提示处于战争；War8 的正常认输许可与自动接受均为真，但 Python 将执行限制在几类紧急战局，导致请求在进入原生执行器前被拒绝。查询可用不代表提交链已经接通。

`machine_id: 4-8e1c2f1861`；观察约 `2026-10-18T14:20Z–14:48Z`，源码接线整理于 `2026-10-18T14:57Z` 后。原 R0020 未执行认输、提交礼仪修改或采用圣地；CK3 正常退出，public0、host1、keeper0分别保留。后继实机结果须另记，不能用下面的 Python 检查授予业务成功。

## 如何使用已有入口

先从当前快照确认玩家、战争完整 ID、攻守方及主战领袖身份，再调用 `ck3_query_war_termination_options`。阅读当前 `options.surrender` 的原版许可、实际结果方向和可观察代价，确认接受后，以当前实际 `expected_revision` 调用原工具。普通防守方投降对应 `attacker_victory`；进攻方投降对应 `attacker_defeat`，不能固定写成同一种结果。

该路径要求精确版本和 EXE、存活玩家、暂停且地图就绪、当前完整 WarID、本人为主战领袖，以及同一快照、公开与原生 revision、连接代次和场次所绑定的原生查询。`context_constructed`、`native_validator_passed`、`available` 和可观察的 `auto_accept` 必须为真；传入战争分数、宣战理由或显式意图都不能替代这些许可。

受管 `native_campaign` 的公开快照没有策略缓存字段，驱动通过已有 `_war_termination_cache_for_snapshot` 严格投影刚才的原生查询。不能因为公开字段缺失就补造许可，也不能把旧场次的查询直接带入后继。

## 一次提交与后验

发送前以持久受管状态或 episode、玩家完整 ID 和战争完整 ID 为身份，独占写入并 flush/fsync once claim。请求、原始 packet 和原生结果各有固定路径；结果未知时保留 claim，改变 request、revision、连接或重新启动驱动都不解锁重发。原自动退战路径同样拒绝重复提交已经被显式认输占用的战争。

实际发送继续使用现有固定 `surrender-war-N` 命令及原生 owner 线程、帧稳定、参战者、主战领袖和原版 resolution validator；没有新增 DLL、任意原生入口或绕过业务 Can 的分支。ACK 后战争仍在时只记 `submitted_pending`；只有独立同身份后态中完整 WarID 已消失，才记动作 `applied`。人物、信仰、领地和资源的具体损失还要分别读回。

`auto_accept=true` 不会被改写成已观察到对方响应。CB 专用条款不可观察时继续记录 unavailable，规划者需要另外核清脚本与当场状态；本接口不替调用者作投降收益比较。

## 本轮检查范围与来源

八项新行为检查覆盖普通防守方、过期与身份反例、原生许可否定、自动策略保持拒绝、未知结果持久拒重发、ACK 后战争仍在，以及真实生产 MCP 协议到 Service/Driver 的调用。快照和传输边界为合成输入，没有执行游戏。另用 R0020 冻结查询走生产缓存投影，验证实际 `native_campaign` 绑定；这也不是新实机提交。

来源包：`C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v5-20261018/mcp/explicit-surrender-a01/HANDOVER.json`，4147B，SHA-256 `2f52c6c628bb3a18869cef8ab60de8df579905cceebeb28623b5384f3c3c3f4e`。补丁23361B，SHA-256 `2ed557191a75663ae4f1e7e5b8a36d8f67ba7b58c45588f5135c7ea9c877fe55`。八项检查及冻结查询回放的精确回执身份在该清单中，原失败检查保留。

实现位于 `bridge/explicit_war_surrender_v1.py`、`bridge/native_driver.py` 与 `bridge/service.py`；使用既有 `mcp_server.py` 工具注册。原游戏命令链和自动应急策略保留，当前新增业务资格仍待后继实机读回。

## R0021 实机补注：普通显式认输已完成

`machine_id: 4-8e1c2f1861`，**2026-10-18T15:23:49Z**：`ck3_surrender_war(8, expected_revision=3)` 从正常防守方查询单次提交，原查询结果为 `attacker_victory`。首 ACK 后战争仍在，记 `submitted_pending`；未重复发送。**15:24:07Z** 独立快照 `revision=4/native_revision=3` 中 `active_wars=[]`，虔诚 `20000→19655`，坎特伯雷 `355` 前后仍由玩家 `15893` 持有。CB 专用条款及对方响应不可观察的字段保持未知；其它战争影响另看实际领地与资源读回。

这为普通显式入口补上游戏内业务后验；自动投降策略的条件没有扩大。随后实际修改主流礼仪 `13` 花费 `300`，采用因管理身份失败而未提交，详见 [R0021 的规划经验](faith-and-power-r0021-agent-experience-12004.md)。精确原件、时间及 SHA 见同名 `.sources.json`；独立实验不构成自然战役全策略资格。原 host1、public0 与 CK3 normalOS0 分别保留。

## R0022：认输后编辑主流礼仪的核心信条，并正常采用

`machine_id: 4-8e1c2f1861`，2026-10-18 R0022 再次经新鲜原查询单次认输 War8；初 ACK 为 pending，独立后态战争清空，虔诚 `20000→19655`。坎特伯雷355保留，Jazira6707归对方12908，投降实际支出345；这不是无代价退战。

随后在保留自身 Faith 宗教领袖的明示准备下，编辑原主流礼仪13的一个核心信条，实际支出300；再以原Can真、bypass0正常采用坎特伯雷4，支出1000。Faith50圣地5→6，旧七Faith等级及库存ID22保留，Faith50/Religion19/礼仪13保持。两次确认分别由独立实际take记录，未重演、未执行键鼠兜底。完整机制与规划边界见 [R0022经验](faith-and-power-r0022-agent-experience-12004.md)及其sources；原public0/host1/CK3normalOS0分别保留，无新恢复资格。
