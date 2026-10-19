# C3 warm LIFE opening：T0 与当前 App 锚点

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-19 的同 Game SDK 恢复中，实际 C3 SEM111 为 `native:38/revision2/date_raw53144760`，角色31254、episode `native-31254-6271ac8cd441`、connection4。Game 为 PID214568 / birth FILETIME134368503807325674，当前 App 及原句柄来源由 [紧凑软件资格](evidence/c3-warm-life-opening-classifier-qualification01.json) 的实际111、C3 pair与launch pins固定；观察 UTC 见该回执。

原 MET110 已按原算法零 RPC 结算48。后续实际 AUTO117 完整返回 `query-campaign-root-context-v1`，但旧 LIFE classifier 将 App 的 existing-focus opening 日期与影片开局 T0 硬相等，于是拒绝原结果。T0 是 raw53144328；此次 App 在同存档18日处启动，真实 opening 是 raw53144760。不能把拒绝误判成原 Native 动作未知，也不能重新提交117。

有限修复由 [来源绑定生产器](../../tools/g2_saved_campaign/prepare_c3_life_opening_classifier_v1.py) 生成。精确原 classifier 258872字节、SHA `f857613afc0872bffeb6d772025afa0feb76e259d8478e14ccf79f8e7732ecbc`；候选260358字节、SHA `41e348591d7c3dd7f42d39daa71ee7ba8d0b857ca9a399fc5307228b6b126cb0`。候选位于本场 `classifier-c3-warm-review01/root_c3_warm_life_opening_classifier.py`，保留原全部 classifier 函数 AST，仅把最后 dispatcher 改名供新 wrapper 调用。

新 wrapper 只识别此次 root existing-focus 分支：传入 initial frame 必须精确等于原 T0；Game PID必须214568；完整 planning source 必须精确等于真实111 warm tuple。满足时，将 warm frame 传给原 classifier。日期、角色、episode、实际 focus、XP、原 Native 效果与 gate 检查仍由原函数执行。评分、月份、地图/录制准入的 T0 均不修改。纯 classifier 的接口没有 birth 字段，birth 沿既有 C3 owner 保管及源 pins证明，不制造同名输入。

软件资格复现原117拒绝；新结果与旧 classifier 显式传真实 warm frame 的结果完全相同。错Game、错source日期、错episode、缺focus、负XP、错result日期六个变体均拒绝，实际115的非 LIFE 分支结果保持相同。第一遍离线资格因未把实际冻结 SDK 加入工具进程的 import 路径而失败；显式读取 P37C freeze 的 source_root 后通过，没有变更运行 SDK 或业务守卫。

唯一 runtime owner 可使用既有 `install_result_classifier` 与 `reconsume_original_response` 核验原117，零新增 Native/MCP调用。安装前须将候选相同字节 create-only 复制到 runtime 原目录的独立新文件名并核对上述 SHA，再安装该路径：原 classifier 有按 `__code__.co_filename.with_name(...)` 定位的战斗/路线 helper，安装在 review 子目录会改变其相邻路径。本文及软件回执不宣称实际安装或恢复已完成。后继实际结果应另行追加。

这次暴露的通用经验是：影片/评分 T0、录制原始准入，以及当前 SDK 的 opening 观测，具有不同有效期。后续常规 warm 恢复应显式保存当前 App opening frame，避免把它塞回 T0。此候选只关闭此次真实 C3 变体，未宣称一般 warm 锚点重构已部署。紧凑证据于2027-04-17复核保留用途。

后继实际读回：119已以既有原件核验路径确认原117，零新增MCP/Native调用，见 [本地恢复回执](evidence/c3-local-classifier-recovery-readback01.json)。原T0保持不变。
