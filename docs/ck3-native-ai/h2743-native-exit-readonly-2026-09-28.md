# Robert h2743 原生退战选项只读复验（2026-09-28）

从[精确接收与无启动配对](h2743-onedrive-exact-input-2026-09-28.md)的四份 SHA 校验原件建立独立 `attempt-02`，使用 CK3 1.19.0.6 原版 EXE、原 DLL、`xar_off/ordinary_campaign_succession` 配置冷启动。启动前新鲜 Steam 画面人工确认“离线模式”，本机任务总线独占屏幕；只运行一次 `ck3_take_snapshot`、`query-war-termination-options-16777231` 和查询后快照，没有提交退战、时间推进或其他游戏动作。[跨机可读的精确摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-H2743-EXIT-20260928.local-h2743-options.json)保留原件身份与外置字节哈希。

第一次 `attempt-01` 将地图等待上限设为 360 秒，尚未进入可查询帧就退出；受管会话正常清理，原件与派生存档哈希不变。它保留为启动时限 RED，不算机制失败。新建的 `attempt-02` 以 900 秒只读等待取得 `native:3`、public/native revision `4/3`、连接代 `1`、日期 raw `53217264`、Robert `29829`、WarID `16777231` 的 paused 帧。查询前后快照 ID 和日期相同，查询后战争仍 active；进程退出码 0，CK3 PID 清零，源与配对存档 SHA-256 均保持 `A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9`。

| h2743 项目 | 原生当帧结果 |
| --- | --- |
| 战争身份 | Robert 为主防守方，对手 `30097`，目标 title ID `2128`；CB `individual_county_de_jure_cb` index 17，已持续 1101 天 |
| 战争分数 | 玩家视角 `-12`，进攻方 `+12`；进攻方分项为占领 `+39`、计时 `-27`、战斗与囚禁均 `0` |
| 投降 | 原生 validator 通过、当前可用、收件方会接受；结果类别 `attacker_victory`，但 CB 特定实际条款不可观察 |
| 白和平 | CB 定义上允许，但**当帧原生 validator 未通过**、不可用；不能据定义推断可以点击 |
| 玩家胜利 | 当帧原生 validator 未通过、不可用 |
| 近端战况 | 玩家可控军 `83886367` 在 2614；敌军 `50331920` 正围攻玩家附庸省份 2628，剩 1 天，另一敌军 `83886484` 正向该省移动；该战争行的双方兵数为 `null` |

原生投降选项的 AI acceptance 原始值 `-8700000/100000=-87`，但同时 `auto_accept=true`、实际 `recipient_response.would_accept_now=true`；因此使用最终原生接收结果，不单独以负数判定拒绝。白和平的原始 acceptance 为 `-2990110/100000=-29.9011`，同时 `auto_accept=false`，且更前面的原生 validator 已拒绝。生产只读观察器在精确查询后快照上返回 `native_legality_observed_material_comparison_open`，没有 `recommended_outcome` 或 `action_literal`；投影外置回执 SHA-256 `D1F142A119A9F01134EC377358C5A176DFFBD7AAB1CFAA92205D13ECD2063E22`。

远端随后提供的[R0264 h2825 独立读口](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-H2743-EXIT-20260928.r0264-h2825-war-options.json)在 15 游戏日后看到相对分数 `-24`，投降仍可用、白和平与胜利仍不可用。它是另一个检查点、DLL 和日期，不能填 h2743 的未知条款，也不能把两帧分数变化归因到某一项未经观察的战斗或围城写回。

额外对 h2743 原始存档做 Rakaly 0.8.19 只读解包，并复用[已有保存层投影器](../../ck3_autonomous_player/tools/project_war31_save_material.py)读取同一目标 title 与双方资源基线。解包文本 SHA-256 `1F12D756D3643CFE7AC7D4A13ED1F39A95EBC508633B63415D6706C1BA71F233`，外置投影结果 SHA-256 `EB8A8737FCB67DCE700474E65D6063BAAD7334A45483263E0F3F22CCA8085FD3`。在 `1075.1.12`，`c_foggia` title `2128` 的 holder 仍是 Robert `33435`，de-facto 上级 title `2141` 的 holder 是玩家 Robert `29829`；直属子 title `b_lucera` 持有人 `33435`、`b_larino` 无 holder、`b_vieste` 持有人 `43703`。Robert 的金币／虔诚／当前威望分别为 `111861020/40832500/253090010` 原始值，即 `1118.61020/408.32500/2530.90010`；Landolf 分别为 `22861397/34640000/85874500`，即 `228.61397/346.40000/858.74500`。两人关系块仍有该 WarID，没有休战槽。这些是 h2743 **行动前保存层基线**，不是投降后的变化或同一原生帧资源读口。

原版该 CB 的 `on_victory` 会创建征服型 title/vassal change，调用 `setup_de_jure_cb` 与 `resolve_title_and_vassal_change`，随后执行参战方 fame/prestige 与停战效果（`00_dejure_war.txt:435–497`）。[同一战争早期的一次真实投降](war31-r0197-one-shot-live-result-2026-09-28.md)确实使 `c_foggia` 与 `b_lucera` 转到 Landolf、Robert 当前威望净减 30、Landolf 累计名望净增 30，并在保存层出现 `30097 → 29829` 的定向休战。h2743 的原始 title holder 仍与早期匹配，所以这是**有具体先例的风险情景**；它仍不能充作 h2743 真实投降条款，尤其不能把六天后的资源净变化当成即时效果。

**下一项决策缺口**是同一当前帧的 CB 特定领地/封臣变化、双方签名资源、定向休战，以及可比较的继续作战风险。早期 R0197 一次性授权下的真实投降可作为同一战争/CB 的历史结果参考，却不是 h2743 或 h2825 的反事实结果；授权已消耗，不得重用。本次结论只提高合法性和即时风险输入的确定度，不让智能体因为“可用”便自动投降。
