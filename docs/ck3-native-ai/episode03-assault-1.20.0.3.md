# 第三期围城：1.20.0.3 破墙、强攻及证据边界

2026-10-02 的只读研究确认：当前 **1.20.0.3** adapter 已有破墙状态、强攻日进度/预计损失、完整 start/stop 原生校验器与动作后回读。第三期的普通围城及强攻预览无需新通用端口。强攻实机对照是可选扩展，须取得新鲜合法破墙样本后单独采集；本研究没有启动游戏、提交动作或采集桌面。

## 版本与最小静态证明

目标为 Steam Crozier **1.20.0.3 / build25652598**。安装文件 `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe` 为 **101039736 bytes**，SHA-256：

```text
94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6
```

独立 [.3 descriptor](../../ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12003.hpp) 与 [.3 factory](../../ck3_autonomous_player/native_bridge/src/ck3_12003_adapter.cpp) 先核验该身份，再复用已审 .2 地址束；[ABI reuse ledger](../../ck3_autonomous_player/native_bridge/research/ck3_1_20_0_3_abi_reuse.json) 及[迁移记录](crozier-1.20.0.3-native-migration.md)保留完整来源。.2 binder 的历史 SHA 与 profile pins 未修改，.2 实机不能外推为 .3 实机。

本次只复验已有围城/强攻中的 **17 处冻结 signature/semantic 字节**，全部匹配；再窄读 9 个已知原生区段，追到所需正向分支及 return。外置完整证据为 `D:/ck3-war-episode03-20261002-a01/research-assault-static-proof.json`，SHA-256 `dc71f10634634447b47b014763301ec8b6ca15e4ecc68184e5f49e7786519f3d`；[入库摘要](episode03-assault-1.20.0.3-static.json)保存输入哈希、RVA 和检查结果。源码读于 `f511a32d0c1a5ca2851c3aa2231918b5a2974fab`，相关 9 个源码/测试/ledger 文件与隔离树基线 `6a837a1ecd9b027170f607242f6f02724908dc14` 逐字节一致。

| 对象 | 本 build RVA / 偏移 | 最小证明 |
| --- | --- | --- |
| 完整 start validator | `0x29738C0` | kind、存活 actor、完整 SiegeID、围城条件、besieger 所属 actor |
| 完整 stop validator | `0x2973A70` | kind、存活 actor、完整 SiegeID、active、besieger 所属 actor |
| start 围城谓词 | `0x29736E0`，调用 `0x251CF70` | 非 active、breach 非 0、原生未受阻 |
| 强攻预计损失 getter | `0x25205C0` | 当前省份 eligible besieging strength、breach-1 表项、定点取整 |
| 强攻日进度 getter | `0x25207F0` 至 `0x2520B4E` | 兵力按 chunk 向上取整、驻军比例与速度插值 |
| Province / Siege 身份 | Province `+0x788`；Siege `+0x08/+0x0C` | 完整 generation ID、magic `0x53696765`、省份 backlink |
| Siege 字段 | `+0x3D0/+0x3D8/+0x44C` | current work、breach、active flag |

读取工具按单个 `.pdata` entry 导出时，`0x251CF70` 与 `0x25207F0` 会只得到各自前 39 bytes；这不是完整函数边界。外置证明另存连续区段及哈希，包含正向分支；不覆盖先前短区段原件，也不把前缀当作完整公式证明。

离线核验显式使用主树 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，Python **3.14.7**、pytest **9.1.1**。对 [native driver 测试](../../ck3_autonomous_player/tests/unit/test_native_bridge_driver.py)执行 `-m pytest -q -p no:cacheprovider ... -k assault`，普通与 `-O` 各 **12 passed、31 subtests passed**；关闭 bytecode 与 pytest cache 写入。覆盖精确解析、start 必须同时具备 stop 恢复能力、同 SiegeID 暂停回读、ACK 无 flag 切换拒绝、未知/失败强攻状态拒绝继续、强攻一日和速度 1。`-O` 的 pytest 提醒已保存在原始输出；这些结果只证明离线合同。

## 原生合法性与数值含义

开始强攻的完整原生校验器以 `(kind=1, played_character_id, full SiegeID, tooltip=nullptr)` 调用。它要求角色有效且存活、角色可使用该 command kind、围城有效且未处于强攻、breach 非 0、原生围城未受阻，以及角色确为该 Siege 指定 besieger 的所属者。`0x251CF70` 明确把 eligible 围城兵力低于当前驻军的情形判为受阻，并保留额外原生省份选择谓词；不以自己简化的“破墙且军队在省份”替代完整 validator。

停止强攻要求有效存活角色、command kind、有效完整 SiegeID、active flag 非 0 和同样的 besieger 所属者匹配。无需等待墙重新完整；也不能把围城自然结束写成执行 stop 成功。

当前安装原版 `game/common/defines/00_defines.txt` 的 `NSiege` 冻结值为：

| 参数 | 值 | 可用于稿件的解释 |
| --- | --- | --- |
| `BASE_SIEGE_PHASE_LENGTH` | `20` | 基础围城 phase 长度；不是保证 20 天破墙 |
| `BREACH_PHASE_TIMER_LEVELS` | `{-0.1, -0.3}` | 两级 breach 的 phase 时间修正 |
| `BREACH_ASSAULT_TICK_PERCENTAGE_CASULATIES` | `{2.5, 1}` | breach 1/2 的强攻 tick 损失百分比配置，原键确实拼作 `CASULATIES` |
| `BREACH_ASSAULT_PROGRESS_CHUNK` | `100` | 参与兵力按 100 人 chunk 向上取整 |
| `BREACH_ASSAULT_PROGRESS_PER_CHUNK` | `0.2` | 每 chunk 基础强攻 work 进度 |
| `SIEGE_ASSAULT_SPEED_MULT_WITH_ZERO_GARRISON_SIZE` | `5` | 驻军比例趋向 0 时的速度倍率端点 |

已读原生 getter 与上述配置支持以下解释：预计损失取当前 **eligible besieging strength**，用 `breach-1` 选择百分比并整数截断；进度取向上取整后的兵力 chunk，受每 chunk work 和当前/最大驻军比例的插值影响。只有这两个级别的损失表；不能把墙颜色、总在场军力、战争名册人数或其他 build 配置当作同一输入。

这些是暂停帧上的原生投影，没有伤亡累计、逐团归因或未来参战者保证。例如纯配置算术中，1000 eligible 人在 breach 1/2 对应百分比项 25/10 人；这是说明取值的算术例子，**不是本次实机损失**。没有读到最大驻军时，稿件不自行补出精确日进度公式值，直接使用原生 getter 的投影。

[Province reader](../../ck3_autonomous_player/native_bridge/src/ck3_12002_province.cpp)在暂停 rich 帧中原子发布 assault 子域；[Python normalization](../../ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py)进一步校验字段。数值边界：

- `breach_level` 为整数 `0..2`；active 为原生 `0/1`。`walls_breached` 只是 `breach>0` 的派生表示，不包含完整合法性。
- `assault_observable=false` 时所有强攻字段为 null。null 不代表 0，也不代表可开始或已经结束。
- breach 0 时 reader 不调用两项强攻 getter，发布 daily progress/casualties 为 0 并仍读取原生 can_start/can_stop；此帧不能称作合法强攻预览。
- `assault_daily_progress` 是 `raw/100000` 的 work 增量投影，非完成百分比；允许超过 `raw=100000`。只有 `progress_fraction.raw` 被限制在 `0..100000`。
- `current_work`、`total_work`、强攻 daily work 为非负 Q100000；预计损失为非负 int32。`days_left=INT_MAX` 留为 unavailable/null，不能显示“还剩 0 天”。
- public `besieging_army_id` 只在完整原生 CArmyID 唯一匹配一个公开 CUnit 时发布；eligible 围城兵力与某支军队当前总人数必须分别保存。

原版 `game/gui/window_siege.gui` 也以 `Siege.ShowAssaultButton`、`Siege.EnableAssaultButton`、`Siege.GetAssaultButtonTooltip`、`SiegeWindow.StartStopAssault` 构成显隐、启用、原因与动作合同。画面上的按钮和原生可用 flag 可以互证；只有按钮画面不能替代精确 SiegeID 与 action 回读。

## 当前 bridge 的查询与动作路径

暂停后使用已存在的 MCP `ck3_take_snapshot()` 或 `ck3_get_war_state()`，从 `active_wars[].objective_province_states[].active_siege` 取该战争目标的有限省份集合；不发明 query-assault MCP。采样绑定同一 `snapshot_id/revision/date_raw`、WarID、ProvinceID、完整 SiegeID，以及可观察的驻军、eligible strength、工作量、breach、active、can_start/can_stop 和军队身份/当前人数。

现有能力为 `game.state.war-objective-assault`、`game.command.start-assault-N`、`game.command.stop-assault-N`。[MCP start/stop](../../ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py)分别接收 `siege_id` 与 `expected_revision`；[native submitter](../../ck3_autonomous_player/native_bridge/src/ck3_12002_military.cpp)重新校验角色和 Siege/Province backlink，使用原生 command kind `0x0E` 提交，不直接改内存 flag。

[Python action 实现](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py)在暂停可观察帧检查 can_start/can_stop，再提交并等待 **同 WarID、ProvinceID、完整 SiegeID** 的暂停 active flag 切换。`start_submitted/stop_submitted` 是提交回执；只有后置条件成立才返回 `assault_started/assault_stopped`。该分支没有独立承诺日期不变，采集者须另验动作前后 `date_raw`。

active 强攻推进已有一日上限、速度 1 与暂停后重读；running 帧会抑制 rich siege，不能以运行中的 null 宣称围城结束。已成功 started 但当前 siege/assault 不可观察，或上一强攻 slice 失败且状态仍未知时，现有 lifecycle 合同拒绝继续推进。事件中断、日期不足一天、身份改变或围城结束须单列，不能凑成完整“一日”或 stop 成功。

## 有限采样路径与稿件可用条件

第三期基础路径只需：**暂停基线 → 普通围城一日 → 暂停回读**。两端保存同目标围城工作量、日期、驻军、eligible strength、军队人数及原始画面；实际推进的日期差决定可说“一日”还是“事件中断”。breach 0 且 can_start=false 本身是有效的“目前不能强攻”画面，不必为本期强行制造破墙。

已有 [.2 F21](ck3-1.20.0.2-r3-war-and-siege-live.md)记录普通围城同 SiegeID 两帧：省份 `2609`、SiegeID `67108919`，eligible `3010`、驻军 `500`、fort `3`，日期 `53169216→53169240`，work raw `450000→900000`、总 work `32500000`，breach 0、can_start/can_stop false。该证据可解释字段来源和普通围城的历史事实；其版本是 **.2**，没有执行 start/stop，第三期 .3 结果必须另采。旧 1.19 围城及 CAS 原型也不升级为 .3 验收。

可选强攻 A/B 只从**同一已破墙、原生可开始且可停止能力齐全的检查点**分出两个新 attempt，保留检查点准确 bytes/SHA 与配置快照，不修改历史 pins。最小样本为：

| 分支/时点 | 必需证据 | 可支持的结论 |
| --- | --- | --- |
| A0 / B0 | 同存档/配置/EXE；同日期、围城身份、breach、garrison、eligible、军队人数和参与者 | 起点可比较 |
| A1 | 普通围城精确一日后的暂停完整快照 | 普通 work 增量、观察到的人数净变化 |
| B-start | 以 B0 revision 提交 start；原始提交结果及同 SiegeID active false→true；另验日期 | 本次强攻确实开始 |
| B1 | 单日速度 1 后暂停；完整快照、日期、工作量、当前兵力/驻军和中断状态 | 本次强攻进度及人数净变化，可与 A1 对照 |
| B-stop | 若仍 active 且 can_stop=true，提交 stop 后同 SiegeID true→false；另验日期 | 本次停止确实生效 |

两分支基础证据为 6 份逻辑暂停观察（A0、A1、B0、B-start、B1、B-stop）；原始 snapshot 与 action 回执分别保全。只采到一条分支时可说“这次强攻”，不可声称对照优势。若 B1 已完成围城，改采占领者、原战争目标状态及明确 no-siege 完成读回，不再提交旧 SiegeID stop；不能为了补 stop 镜头改写已结束结果。

最低优先选择一支自控、静止、无 combat/retreat 的参战军，原生 eligible 和当前人数均可观察。每个分支的 event、分兵/合军、参与者变化、驻军变化和战斗/补员/损耗均记录。`army_after-army_before` 只能叫**观察到的人数净变化**；要叫“强攻造成 X 人阵亡”需另有原生归因或清晰排除混入因素的证据。当前 projected casualty 字段不能承担这项归因。

本期文案可使用新 .3 暂停帧中的“墙有缺口”“原生目前允许/拒绝开始强攻”“预计日进度/预计日损失”，以及新普通围城两帧的实际 work 增量。只有完成 B-start/B1 才可描述本次强攻结果，只有两条起点一致的分支才可描述这次对照；不推成普遍最优策略或无损保证。

## 观测缺口与最小复用

目标在当前战争 `objective_province_states` 内时，没有阻止上述最小样本的缺口。直接复用现有快照、start/stop 和一日 slice 即可；最大驻军没有独立发布也不阻止使用原生日进度投影与实际 work 差。

当前快照不提供强攻逐团累计损失归因，也不承诺在任意非战争目标省份发布相同 rich assault 行。若未来明确要任意目标，先将现有 `ReadObjectiveProvince` 和同 revision/date 的 local-province query 合同复用到 .3 descriptor，限定一个指定 province、一次暂停 owning-thread 读取及完整 SiegeID round-trip；不需要第二套强攻命令。若未来明确要精确伤亡归因，再窄查并独立暴露原生损失 ledger；当前 episode 只需外置采样比较器，绑定两端 snapshot 哈希并把 projection 与 observed delta 分开，无需扩大 native 能力。

截至本报告，**静态与离线合同已核验，1.20.0.3 强攻开始/一日伤亡/停止实机未执行**。所有 live 采集由本期唯一实机执行者在新 attempt 中进行，原片、RED、中断与旧证据原样保留。
