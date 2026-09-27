# 普通战争战中主动撤退：队列生产端的有界排除与下一采集合同

日期：2026-09-27。对象是 CK3 1.19.0.6 Steam build 23530548，EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
本包只读磁盘上的 EXE 和本仓库源码；没有启动、附加或修改 CK3，也没有新增实机样本。
它接续[主动撤退总专题](active-combat-retreat.md)与[先前两处非移动入队点](indirect-queue-producer-non-move-candidates-2026-09-27.md)，不改写历史结论。

## 新的静态判定

对 `0x1800000..0x1900000` 的 `0x973E00` 直接调用候选，本包只选六处尚未归因的入口。
[exact-build verifier](../../ck3_autonomous_player/native_bridge/research/verify_war_retreat_queue_candidates_static.py)
逐处核对真实 `call` 目标、两次 RIP-relative vtable 装载、MSVC Complete Object Locator、
同名 RTTI 与真正 `CMoveUnitCommand` 主 vtable `0x432BF18` 的不相等。结果如下：

| 提交点 RVA | 构造窗口 vtable RVA（主 / 次） | exact RTTI 名 | 有界结论 |
| --- | --- | --- | --- |
| `0x183E484` | `0x4323668 / 0x4323638` | `CCreateFaithCommand` | 创教命令，非移动。 |
| `0x183E674` | `0x4093A78 / 0x4093B10` | `CSetPrimaryTitleCommand` | 主头衔命令，非移动。 |
| `0x183E7BA` | `0x40939B0 / 0x4093A48` | `CSetRealmCapitalCommand` | 首都命令，非移动。 |
| `0x183E918` | `0x4322710 / 0x43224B8` | `CSetCourtTypeSettingCommand` | 宫廷设置命令，非移动。 |
| `0x187BBDB` | `0x43305B8 / 0x4330650` | `CHireHolyOrderCommand` | 雇佣骑士团，非移动。 |
| `0x187C7F1` | `0x4330680 / 0x4330718` | `CHireMercenaryCompanyCommand` | 雇佣佣兵，非移动。 |

四个 `0x183E...` 提交点虽然处在战争/角色更新附近，不能仅凭代码邻近或共用
`0x973E00` 判为军队撤退。两个 `0x187...` 提交点处在军队调度邻近区域也一样。
这些六处只是所选样本；先前的 35 处是该地址范围的原始 `E8` 候选清单，不是已经按指令边界、
业务来源、动态命令类型完成分类的 35 个普通战争 AI 选择。空对象 factory `0x26C6F80`
的 direct-call/absolute-pointer 查询仍未给出上游；本轮未恢复它的动态消费者。

复核命令只读文件：

```text
<verified-python> ck3_autonomous_player/native_bridge/research/verify_war_retreat_queue_candidates_static.py --exe <exact-ck3.exe>
```

本机复核 PASS。detached `D:/wrt` 没有相对 `tools/.venv`，故显式使用并先确认主工作区的
`D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`；`disasm_ck3.py --help`
和本 verifier 均正常加载 `pefile`、`capstone`。EXE 来自
`C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe`，由 verifier 校验整文件 SHA。
没有宣传工具链任务，不涉及 `xar-promo` 环境。

## 普通战争 policy 仍缺的链

已经闭合的是引擎通用路径：`CMoveUnitCommand` 可由 `0x973E00` 入队，
apply 的 `0x26B4710` 遇 active CCombat 会经 `0x2308850` 执行撤退；
`0x2308250` 提供同一 legality。已查的普通 representative/follower 移动在 active combat
时提前跳过；raid、barter、counter-raid 的任务来源不能替代通用战争败势选择。
第六日种子开始的 26 日纯 AI 观察只看见败后撤退，未出现普通战争 AI 的战中自选撤退。
这些证据没有闭合 `active CCombat / battle odds → voluntary choice → target Province → move producer`，
也没有证明此策略不存在。先前 normal/desperate `0.5/0.4` 是接战阈值，不是战中撤退阈值。

游玩智能体的[策略实现](../../ck3_autonomous_player/src/xar_autoplayer/strategy.py)已消费
`battle_control_snapshot_v1.legality`：当同一观察日只因 `too_early` 不可撤退时，
以 `earliest_day_gate_date_raw` 调整战斗观察的下一决策日（约 `9323..9359` 行）。
它没有在 `strategy.py` 中选择 `preview-active-combat-retreat-v1` 或
`order-active-combat-retreat-v1`；这两个 typed 能力在 bridge/driver 层已实现，
目前是可被明确调用的动作能力，不是当前自动策略的主动撤退分支。
因此“消费 native legality”目前只成立于战斗观察日程，不能说策略已根据整场胜率选择撤退。

### 接入游玩智能体的最小自有策略门

接线不必等原版 AI 的未知 `odds→choice`；它应明确命名为**我方自有战中撤退策略**。
现有 [有界整场试算](general-battle-strategy-forecast-2026-09-26.md)已经用于接战准入，
但它的 `contact_admission` 是**开战前**的风险预算，不可反过来把“接战不准入”直接解释成
“已经开打就该撤退”，也不可复用旧接战帧作为当前战斗状态。最小实现合同是：

1. **当前输入**：同一个 paused revision 上绑定 WarID/CombatID、选中 CUnit/Army 全 ID、
   双方当前 roster、phase/day、剩余兵力/软硬损失、当前可参战兵团及其有效属性；
   仅接受以该**战中当前状态**为起点、显式记录固定参战者/未来事件等假设的有界 forecast。
   一旦 roster、日期或 revision 改变，重新取数试算。不得把开战前 v3 输入和已损耗战斗混用。
2. **自有决策**：同一帧比较 `continue`、已证实可到达的 `reinforce` 与 `retreat`
   的结果/损失区间；撤退的追击损失、路线敌军与战役价值如果还没有可信量化，
   在回执中单列 `unknown` 并使用明示的保守策略阈值，不把研究核的胜样比例写成原版胜率。
   这一步可以在证据有限时继续作有界决策，但不能简单求 `1-contact_admission`。
3. **native 可执行门**：所选 CUnit 必须当前可控、仍属于同一 active CombatID，
   `0x2308250` 投影的 `legal_now=true`，且 scope/affected/unaffected 与预期一致。
   先以已完成完整转移验收的 homogeneous-owner full-side 为自动动作首批场景；
   mixed-owner owner-subset 仍须其单独 live 后置条件验收。目标省由我方策略选出，
   再对该省做 exact `PreviewMoveArmy`，绑定路线与一次性 token。
4. **命令与读回**：带同帧 revision/CombatID/scope/token 走现有
   `order-active-combat-retreat-v1`/`SubmitMoveArmy`；ACK 只记 `verification_pending`。
   新 paused revision 必须核实退走 CUnit 的 route/target/state、原 CombatID 的 winner/phase
   或 owner-subset 留队、相应追击结果。读回不一致就保存 RED 并重新观察，不重复盲发命令。

这段是待实现的策略合同，不声称现有 `strategy.py` 已有战中 forecast 比较或自动撤退动作。
原版 AI 的阈值和目标评分依然单独保持 unknown。

## 下一次有界采集

Steam 离线画面尚无可核验的新鲜帧，本包不做实机。恢复门禁后，以无玩家派令的原版普通战争
active-combat 场作独立 attempt；优先从自然生产命令的一刻取证，不再重复收集仅有战败后
`retreating=true` 的存档：

1. 进入 main phase 前冻结 save、EXE/DLL、WarID、CombatID、CUnit/Army 完整 ID、owner 与双方 roster。
   观察窗口按日有界，任何无命令窗口都是该 fixture 的阴性结果，不外推到全游戏。
2. 只读观察 `0x973E00` 入口：先用两个 vtable 地址点和 RTTI 过滤
   `CMoveUnitCommand`，再记完整 UnitID、kind、target Province、mode/route、flags、
   生产 caller return RVA、日期与线程。flags `7` 只是 AI 线索，必须再排除 UI、脚本、任务型控制器。
   原对象指针会被 clone，不得单靠指针配对后续执行。
3. 同一命令记录入队回执及 clone/队列序号，再在 `0x26B4710` apply 入口和
   `0x2308850` 分派前后核对 payload、同一 CUnit/Combat、active 状态、目标与 native legality。
   若没有可靠序号，只能标记多键配对为候选，不能宣布因果闭合。
4. 若捕获到 ordinary-war active move，再上溯真实 producer 的控制流：读取它使用的
   battle odds、战损、兵力或别的量、比较边界、候选省枚举与目标评分；在相同暂停帧
   绑定输入。单一已执行 target 只能证明选择结果，不能证明它如何排序或 tie-break。
5. 动作后用新的 paused revision 查 route/retreat state、旧 CombatID 的 full-side 或
   owner-subset transition，以及其余军队继续战斗的情况。queue ACK、仅一处状态位变化、
   敗后自动撤退都不能单独标成 AI 自选主动撤退。

在这条 producer→apply→postcondition 链出现之前，生产 opponent model 的
`generic_war_ai_voluntary_retreat_policy` 与 `generic_retreat_target_score` 仍应为 `unknown`。
游玩智能体可以继续使用已核的 native legality 和自有整场胜率模型设计撤退策略，
但应把自己的策略明确标记为自有策略，不能借未证的原生 AI 阈值背书。
