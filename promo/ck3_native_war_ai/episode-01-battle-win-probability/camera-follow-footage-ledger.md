# 第 1 集：墨西拿战斗镜头跟随与实机素材

2026-09-24；精确游戏版本 CK3 1.19.0.6；原版 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。本次从先前保全的原版接触点存档重新加载，`CombatID=16777218`、开战 `date_raw=53146248`、战斗位置省份 2633。运行目录为 `D:\workspace\ck3_native_war_ai_promo_work\episode01-full-edge-attempt-005`，原始录像、失败片段、逐日请求/响应、桌面截图和编码日志全部保留。

视频与游玩智能体使用同一个 `war_hotspot_camera.py` 选择器。本场 1–31 天均从原生 `active_wars` 选中交战中的省份 2633，解析为 `b_messina`；原生 `center-map-on-landed-title-v1` 回执核对稳定键、revision、镜头停稳与 postcondition。录像开头的 `opening-camera-follow.json` / `.png` 证明自动选点和实机画面吻合，地图中央可见双方军旗。

首段 `gameplay-hotspot-follow-full-battle.mkv` 的录制在第 17 天收到 `state_changed`：鼠标被移到屏幕边缘后，CK3 持续滚动地图，说明居中回执不能保证几秒后的画面。这次 RED attempt 原样保留。随后给视频与智能体共同流程加入前台 CK3 客户区鼠标停放；视频再增加镜头开始和停留末尾的军旗像素门禁。`resume-d17-r2.mkv` 是第 17–19 天续拍，`resume-d20-r3.mkv` 是第 20–31 天及终局续拍；两段的逐日门禁均通过。最后一天战斗已结束，镜头切换到战争目标，其尾部不作为战斗标记可见区间。

1 秒间隔的视频审计结果：首段前 131 秒可见（131/139 样本），第 17–19 天续段全 29.433 秒可见（30/30），第 20–31 天续段前 109 秒可见（109/116）。`clean-battle-edit-plan.json` 只选 `[0,130]`、`[0,28.4]`、`[0,108]` 秒，留出边界余量。由 `assemble_verified_battle_footage.py` 拼接的 `gameplay-messina-full-battle-clean-v1.mp4` 为 266.4 秒、77,025,802 bytes、SHA-256 `1BF6FD2E3B35DF5E0B43F8EE7D595422E3BE959F156409A33829133B8F6D9A02`。拼接后独立再次以每秒一帧审计，**267/267 样本可见战斗标记**；审计文件为同目录 `gameplay-messina-full-battle-clean-v1-visibility-audit.json`。自动逐秒抽样与原始截图人工抽看不能替代对最终成片按 1× 完整人工观看和签核。

**证据边界：**这条完整镜头是从同一接触点存档启动的**独立重放**。它与原始 31 天战役在第 6 天起数值分叉，虽然有相同 CombatID 和位置，也不能把重放第 12/22 天的画面当作原始战役那两天的数值证据。原始战役的逐日数字只用原始原生回执与数据图卡讲解；重放片段要显式标注“同存档独立重放 / 第 6 天后分叉”。这份镜头素材仅证明拍摄视角与实机可见性，不推出整场胜率百分比，也不补足尚未闭合的事件 effect、参战变更和终局概率模型。
