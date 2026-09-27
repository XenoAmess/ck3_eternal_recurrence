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

由此可构造精确只读 V3 查询字面量 `query-combat-simulation-inputs-v3-2629-2630-a-1-83886367-d-1-50331920`。本次三步采样**尚未执行该 V3 查询**，也未运行完整正式规划器或批准接战；H2825 请求的最终实机消费验证仍待下一轮。第二轮托管进程返回 0、CK3 子进程清空，源与预备存档哈希均保持冻结值。
