# H2825 原生同帧围城参与者划分只读复验（2026-09-28）

本机已按[六文件精确接收与无启动配对](h2825-onedrive-exact-input-2026-09-28.md)启动冻结 H2825 存档，使用 SHA-256 `A520BCB688ED921E8DA7410D8426E2FE443135F3F0CECBA928791CCBA0243245` 的 R0265 DLL。启动前新桌面截图为 `D:/ck3-research-artifacts/war31-h2825-20260928/steam-desktop-recovery-05/probe-1/steam-moved.png`，SHA-256 `F8F639869274354780631784BBB33DAC16AB80889E19C20312045087A543BB2F`；人工看见时间更新至 05:26 且 Steam 左下为“离线模式”。本机沿用已验证可用的 R0221 注入器，SHA-256 `C89F1A919514A7E664AEE8FAF165B78C693ABA4EA2105289BDA2DB4BAC6A84FF`，与 R0265 报告所列注入器 `521EB12E5B3F8AFCFF01B2B2B8D9D6B6690B24CC59BE7C25E0E101F438766710` 不同。因此本次复验匹配原存档、driver、sidecar、DLL 和游戏 EXE，**不声称完整 R0265 可执行文件组合逐字节相同**。

第一轮 `attempt-01/live-readonly-01` 在地图刚可读、episode 和角色尚未绑定的 `native:1` 过渡帧提前触发本地身份断言；这是采集脚本时序错误，不是战争逻辑的失败。它保留了原始 `before-payload.json`，托管进程正常退出，CK3 子进程清空，源及预备存档 SHA 均未改变。第二轮新建 `attempt-02`，官方 prepare/rebind/preflight 再次 READY，并等到 episode、角色、日期和战争帧同时匹配才读数据。两轮均未提交游戏内动作。

第二轮只执行三项原生只读步骤：`query-army-strengths-v1`、`preview-move-army-83886367-to-2629`、`query-route-contact-horizon-v1-83886367-to-2629-h-2-50331920-83886484`。每项返回 `accepted=true/status=available`，绑定同一 `snapshot_id=native:3`、公开 revision `4`、原生 revision `3`；前后日期始终为 raw `53217624`，角色 `29829`、episode `native-29829-2bc2d599f7f9`、WarID `16777231` 均一致。外置原始 envelope、payload、每步后快照、launch plan 和清理回执在 `D:/ck3-research-artifacts/war31-h2825-20260928/attempt-02/live-readonly-02/`，最终快照 SHA-256 `EB61683167284121ACB9F2AB532A6BF5684527098085D7C449268B199A9C5648`。

| 原生观测 | H2825 同帧结果 |
| --- | --- |
| 我军 `83886367` | 当前位置 `2610`；2,329／2,461 人；到目标 `2629` 的路线 `[2614,2618,2624,2631,2630,2629]`，预测到达 raw `53218680` |
| 目标围城军 `50331920` | 战争行与路线读口都在 `2629`，状态 `sieging`；1,462／1,899 人 |
| 场外敌军 `83886484` | 战争行与路线读口都在 `3660`，状态 `moving`；311／311 人；当前路线到目标预测 raw `53219928` |
| 整场敌军名册 | 两支合计 1,773 人；这是整场战争军力，不能直接当作目标遭遇的守军 |

用这三份原生查询及同帧战争行对当前 `strategy._siege_forecast_participant_partition` 做纯回放，得到 `status=available`、`defender_army_ids=[50331920]`、`offsite_hostile_army_ids=[83886484]`、`offsite_arrival_risk=unmodeled_after_target_entry`。场外军按**当前路线**比我军晚 `1248` raw ticks（52 个游戏日）到目标；这只证明当前路线下目标进入时的假设划分，不证明交战期间不会变更命令或增援。回放回执 `partition-replay.json` SHA-256 **`F50D944E7942F93AB9F59E532F426F2C94E0FAAD61CB91B2A32C5B65B82F8BEF`**，其中绑定了四份原始同帧输入的 SHA。

由此可构造精确只读 V3 查询字面量 `query-combat-simulation-inputs-v3-2629-2630-a-1-83886367-d-1-50331920`。第二轮三步采样尚未执行该查询；托管进程返回 0、CK3 子进程清空，源与预备存档哈希均保持冻结值。

## 第三轮：原生 V3 输入读回

新建 `attempt-03`，再次使用冻结原件、官方无启动配对和精确 R0265 DLL。启动前截图 `steam-desktop-recovery-06/probe-1/steam-moved.png` SHA-256 `5297E8465388F43BA98EE9B3911F7B813AC6C7DE3887F9556C02BDBC02063F89`；人工看见任务栏时间 05:44、Steam“离线模式”。在同一 `native:3`／revision `4`／native revision `3`／raw 日期 `53217624` 上重新执行三项只读军力与路线查询，运行当前参与者划分，仍得到守军 `[50331920]`、场外军 `[83886484]`。只有该划分通过后才执行上面的 V3 查询。

V3 返回 `accepted=true/status=available`，其 `base_inputs.scenario` 为目标 `2629`、入口 `2630`、攻击军 `[83886367]`、守军 `[50331920]`，参与者政策为 `explicit_hypothetical_fixed_at_contact_no_reinforcements`。查询绑定同一原生帧；随后快照的缓存状态仍为 `available`，目标、入口、双方 ArmyID、`queried_snapshot_id=native:3` 和 `queried_revision=4` 全部一致。原始 V3 回执 `query-04-payload.json` 为 4,076,271 字节，SHA-256 **`00268510BC447FF1B5D1B085698B45F3B33FB94E81628F1B11D9BAA9A5E63AB7`**；最终快照 `after-04-payload.json` SHA-256 **`037EA98041568374F7CB0A37F6D02200457DBE98388AA9E6FC559316E064E38F`**；简明结果 `read-only-result.json` SHA-256 **`C4C61AB4545BD3CC51898F055A9D1DD98A204D964C6A125943894079A87C9532`**。这些文件均在外置 `attempt-03/live-readonly-03/`，不覆盖前两轮。

V3 `completeness` 同时明确 `monte_carlo_ready=false`、`planner_usable=false`、`active_attack_allowed=false`；缺少载入 playset 验证、AST 求值与原版轨迹保真，并仍列出伤亡分配、追击、终局撤退及阶段事件随机与效果等所需域。因此它证明**假设遭遇的原生输入可读**，不证明整场胜率或批准直接接战。第三轮没有推进日期或提交游戏内动作；托管进程返回 0、CK3 子进程清空，两份存档仍为冻结 SHA。`ck3_plan_turn` 的实际消费行为还需单独只读复验。

## 第四轮：正式规划器自己消费 V3

新建 `attempt-04`，同样通过官方无启动 prepare/rebind/preflight，配对原存档、driver、sidecar、R0265 DLL 和本机游戏 EXE；本机注入器仍是与 R0265 报告不同的已验证 R0221 版本。启动前新截图 `steam-desktop-recovery-07/probe-1/steam-moved.png` SHA-256 `5F4AF9C4A71B61D6E96AA8A2469065A04DEC43A066F336FC4E3A6B7CD8BA407D`，人工看见 06:05 及 Steam“离线模式”。脚本只调用 `ck3_plan_turn`，并仅执行它自己选中的显式只读 allowlist 步骤。

规划器在同一 `native:3`／公开 revision `4`／原生 revision `3`／raw 日期 `53217624` 顺序选出五个查询：`query-war-termination-options-16777231`、`query-army-strengths-v1`、`preview-move-army-83886367-to-2629`、`query-route-contact-horizon-v1-83886367-to-2629-h-2-50331920-83886484`、`query-combat-simulation-inputs-v3-2629-2630-a-1-83886367-d-1-50331920`。五项原生响应均为 `accepted=true/status=available`。V3 原始 payload SHA-256 仍为 **`00268510BC447FF1B5D1B085698B45F3B33FB94E81628F1B11D9BAA9A5E63AB7`**，随后缓存明确为攻击军 `[83886367]`、守军 `[50331920]`、状态 `available`。第六次规划选择了 `preview-move-army-83886367-to-2614`，阶段 `native_war_provisional_defense_short_preview`，理由是先读不能直接接触远方围城军的第一跳路线。采集按预设在 V3 后停止，未执行第六步，也未提交移动、推进日期、接战或投降。

第一项终战读口还把这场战争的 CB 精确读为 `individual_county_de_jure_cb`（database index `17`）、玩家为 defender、当前战分 `-24`。其 payload SHA-256 `4FA460AC977EF9C25C2FAAE5E41630CB146A2903D03860B110CF28B2D721F4BD`；这也让[三名囚犯的 FP3 条款](h2825-prisoner-war-retention-source-2026-09-28.md)对该 WarID 判为不适用。

第四轮完整简明回执 `attempt-04/live-plan-readonly-04/read-only-result.json` SHA-256 `23558C5FAEA9A5C2A81154D3CDFE8AF2E2845F2DBAEF209710E0471CE8AC5C74`，第六计划原始 payload SHA-256 `693FEE2565F15D00C40C5155FF782B65E8E994B3F433C572F7866F5C0ABBDDBD`；清理回执 `session-exit.json` SHA-256 `0E1E585D6B0BC5224C445E6933EAC66460B6986D808DC870E998FA3BB496DB0C`，托管退出码 `0`、CK3 子进程空、源与预备存档 SHA 不变。由此原请求中的**规划器因参与者集合不能成形而直接阻断**已在同源只读复验中解除；尚未证明第一跳移动后的新帧继续、实际战斗或整场胜率。V3 自身的 `planner_usable=false` 和 `active_attack_allowed=false` 没有被提升，规划器走的是风险受限的第一跳预览。
