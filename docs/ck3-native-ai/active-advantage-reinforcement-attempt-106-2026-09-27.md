# 106：增援日日界的优势原调用与原版输出同源对拍

106 从第 11 日冻结存档 SHA-256 `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953` 独立启动 CK3 1.19.0.6，配对保存回执 SHA-256 `DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5`。EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；带优势原调用观测的 DLL SHA-256 `DB4E5EE96EAA72836D3F853618A65A16F7346F6CC6B1E34C0F8E672138589B6E`。这次 begin 同时声明 `candidate_joining_army_id=22`、`capture_runtime_join_width=true`、`capture_runtime_join_full_entries=true`、`capture_runtime_counter_output=true` 与 `capture_runtime_advantage_components=true`，修正了 [105](active-advantage-reinforcement-attempt-105-2026-09-27.md) 漏传候选增援军 ID 的 RED 配置；105 原始证据不改写。

原始独立 attempt 在 `D:\workspace\ck3_native_war_ai_promo_work\episode01-active-advantage-reinforcement-attempt-106`，对照为 [098](active-counter-output-trace-attempt-098-2026-09-27.md) 的同源原版日界。106 `input-freeze.json` SHA-256 `8680F5432705E2DE89755D23265279F0CAD7AB89086C621E2215DC7D006FF8D3`，preflight `FEB288712C9C608F705628B5F6FB4D18C02129664278E43989D669AC71647C6D`，`c106-trace-finish.json` `9DF1DB4763A9CC74FCB66751A8D8353A9427D555247C12F474D0BD6D8A31B24A`。受管推进只跨 `53146488→53146512` 一个日界，主战 day 7→8。trace `status=captured`、`failure_flags=0`，七个边界记录各自 `capture_failure_flags=0`，同一 CombatID `16777218`；整体 `bounded_capture_complete=true`。清理回执 SHA-256 `1B3FC992333B003DDA1F7DC1FD418172BA2A32FA68BCF6D43344EBB1F959E1C5`，`cleanup_ok=true`、CK3 进程树清空。

[106/098 哈希绑定投影](../../ck3_autonomous_player/native_bridge/research/fixtures/advantage_reinforcement_ab_106_098.json)由[只读对比脚本](../../ck3_autonomous_player/tools/project_advantage_reinforcement_ab_106_098.py)从原始回包重建，并核对冻结 save、receipt、EXE、各次 DLL preflight、七个边界、增援与伤害字段。除受管序号、线程 ID、进程内事件 identity token 外，两次完整边界记录逐字段相同；增援宽度原调用三条依次为军队 22、`side=-1/0/0`、基础宽度 `1645/2467/2467`、最终宽度 `1480/2220/2220`。完整入场快照的 side 0 兵团条目从 `27` 增至 `40`，新增军队 22 共 `13` 条，军队列表从 `[16777221,16777231,27]` 变为 `[16777221,16777231,27,22]`。

原版两侧 13 类反制保留向量与 098 相同：side 0 只有 class 8 为 `10000`，其余 `100000`；side 1 的 class 0、1 为 `10000`，其余 `100000`（均为 Q100000）。反制后攻击 `7163402981/1455075113`，伤亡前出伤 `116118762/67660992`，也都与 098 精确相同。优势原调用有一条完整 materialization，`failure_flags=0`：base `-300000`，side 0 掷骰 `7`、指挥官 34320、总项 `4200000`；side 1 掷骰 `8`、指挥官 29829、总项 `5000000`；原版缓存结果为 `-300000+4200000-5000000=-1100000`，单位 Q100000。

暂停帧的输入更新也单独做了[哈希绑定投影](../../ck3_autonomous_player/native_bridge/research/fixtures/counter_refresh_ab_106_098.json)，由[只读脚本](../../ck3_autonomous_player/tools/project_counter_refresh_ab_106_098.py)核验四份 battle-control 原始回包。第 11 日 `active_counter_inputs_v1` 的 side 0/1 职业兵条目数为 `18/14`，第 12 日为 `24/14`；新出现的 side 0 六条职业兵 `176,177,179,180,181,182` 均属军队 22。098 与 106 在对应暂停帧的两侧条目逐项相同。这说明**原版入场后重新查询的同帧输入能看到新增军队**，生产智能体在下一决策帧可重新获取这份原生输入；第 12 日回包已经过该日日更和伤亡，不能倒灌成第 11 日对增援的事前预测，也不能用其伤亡后的数值冒充第 12 日伤亡前入参。

因此可把“同源增援日同时观测原版优势分解与反制/伤害输出”标为已对拍。它仍是**事后单日观测**：`full_mutable_transition_bundle_complete=false`、`original_trace_ready=false`，`forecast_usable=false`；没有证明暂停第 11 日就能预测军队 22 的加入、以后各日的优势、骑士/撤退与伤亡转移，或整场胜率标定。当前生产策略的固定接战分布及风险门继续按各自合同使用，不能把本页静态相等误写为未来预测已闭合。

106/098 都从第 11 日原存档**连续推进**，所以是同条件 A/B。106 在第 12 日连续帧的优势与有效兵团属性，不能直接与 100/104 从第 12 日新存档**重载**后的属性拼成一条无缝计算链；见[重载帧对照](active-battle-fresh-load-frame-divergence-2026-09-27.md)。

复验命令（读取原始 attempt，不启动游戏）：

```text
tools\.venv\Scripts\python.exe ck3_autonomous_player\tools\project_advantage_reinforcement_ab_106_098.py --attempt-106 D:\workspace\ck3_native_war_ai_promo_work\episode01-active-advantage-reinforcement-attempt-106 --attempt-098 D:\workspace\ck3_native_war_ai_promo_work\episode01-active-counter-output-attempt-098 --expected ck3_autonomous_player\native_bridge\research\fixtures\advantage_reinforcement_ab_106_098.json --check
tools\.venv\Scripts\python.exe ck3_autonomous_player\tools\project_counter_refresh_ab_106_098.py --attempt-106 D:\workspace\ck3_native_war_ai_promo_work\episode01-active-advantage-reinforcement-attempt-106 --attempt-098 D:\workspace\ck3_native_war_ai_promo_work\episode01-active-counter-output-attempt-098 --expected ck3_autonomous_player\native_bridge\research\fixtures\counter_refresh_ab_106_098.json --check
```
