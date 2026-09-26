# 原版战争热点镜头跟随（1.19.0.6）

## 共同入口

`ck3_autonomous_player/src/xar_autoplayer/bridge/war_hotspot_camera.py` 是游玩智能体与战争视频拍摄的共同热点选择器。它从当前原生 `active_wars` 快照按以下顺序选择**可观测的陆地省份**：受控军队参战位置、同方其他军队参战位置、受控军队围城位置、同方其他军队围城位置、战争目标的正在围城位置、受控军队**当前行军位置**、行军目的地、战争目标、受控军队闲置位置。行军中的军队在陆地上时镜头跟随其已观测到的位置，不提前跳到远处的目的地；若当前位置在海上，则退回可解析的陆地目的地。多处同级热点按战争 ID、军队 ID 与省份 ID 稳定排序。海域没有领地键，不能成为镜头目标；没有可解析陆地热点时明确返回 `no_observable_land_hotspot`。

省份到男爵领稳定键的映射在运行时只读解析当前 CK3 安装目录 `game/common/landed_titles/*.txt`。本机原版安装的 10 份文件解析出 10,966 个陆地省份；2633 对应 `b_messina` / `c_messina`。这个映射是展示用定位数据，不是战斗胜率模型、路线策略或命令能力。游戏升级后必须重新解析当时安装的原版文件；实际镜头命令仍受精确 CK3 build 和桥接 capability 门禁约束。

## 执行与验收

智能体的 `native_auto_run` 每回合在准备好暂停快照后、`auto_turn` 选择并提交游戏行动之前，调用同一选择器。它使用 `GameplayBridgeService.center_map_on_landed_title_v1` 的展示专用接口，不把居中伪装成 planner-selected 游戏步骤。CK3 在前台时，`camera_cursor_parking.py` 将鼠标停到客户区内部安全位置；受管实例确为全局唯一 CK3 PID 且其可见顶层窗口全部最小化时，返回 `skipped_minimized` 并保持用户鼠标不动。仅处于后台但仍可见、窗口/PID 不明或视觉输入所需的场景不走该豁免。调用仍须绑定快照 revision；原生结果的稳定键、`centered`/`already_centered` 状态和 `camera_center.postcondition_verified=true` 都须成立。镜头失败会以 `camera_follow.status=unavailable` 写入该回合记录，不能伪称画面已对准，也不能替代战斗行动。

2026-09-26 R0222（4cf58b5）实机首次按新窗口规则保持最小化后，后台 heartbeat 达 791，paused native turns 可读，但每回合附属镜头因 `park_foreground_ck3_cursor` 报 `ck3_not_foreground` 而记为 unavailable（attempt-01 正式报告行 274/419/558）。上述窄修复使真实最小化窗口无需鼠标停放即可尝试 native 镜头，并继续要求独立原生居中后置；目前只有源码/聚焦测试，最小化镜头新行为尚待下一轮实机核验。

2026-09-24 复核时发现原先传给热点选择器的是 `native_auto_run` 的压缩 readiness binding，其中战争列表保存在 `_semantic.active_wars`，顶层没有 `active_wars`；因此先前的 agent 接入会返回 `no_observable_land_hotspot`。现已从**同一 readiness revision** 的 `_semantic.active_wars` 建立展示输入，并把成功或失败的 `camera_follow` 持久写入每回合正式报告；发生游戏动作失败时也写进 first-failure 记录。集成测试验证实战热点 `b_messina` 的定位发生在 `auto_turn` 之前；模拟镜头不可用时，回合仍继续执行原本的游戏动作。此测试证明调用与隔离逻辑，不替代长期原版实机 agent 运行验收。

视频拍摄使用 `promo/ck3_native_war_ai/integration/war_hotspot_camera_capture.py`，对每个要进入成片的推进节点读取原生快照、复用同一选择器、向当前 capture session 提交展示专用 MCP 调用，并将请求、响应、热点选择和桌面截图按字节哈希保全。逐日录制器 `capture_battle_with_hotspot.py` 在每个镜头开头和停留结束各截一帧；本集墨西拿战斗使用 `battle_frame_gate.py` 将经人工确认的军旗模板与地图中央区域对照，分数低于当次冻结门槛即停止录制并保留 RED attempt。录制前及热点变化后还须检查原始截图：目标战场或围城标记位于有效地图画面内，主要 UI 未遮住解说重点；原生居中回执不能替代像素层检查。镜头失锁或截图证据缺失时，相关片段不能标为合格实机镜头。

首次原生实证：`D:/workspace/ck3_native_war_ai_promo_work/episode01-full-edge-attempt-004/ck3-output/interactive-requests-responses/d28-center-messina-v1.json` 对 `c_messina` 返回 `centered`、`capital_province_id=2633`、`settled=true` 与 `postcondition_verified=true`；同 attempt 的 `screen-20260924T082512539446Z.png` 显示墨西拿海岸和战斗标记在画面中央区域。`attempt-005/opening-camera-follow.json` 对共同选择器给出的 `b_messina` 回传精确省份 2633 的已停稳镜头。该 attempt 的首轮长录在第 17 天因鼠标停在屏幕左上边缘而发生地图滚动；原生前一日 `already_centered` 回执不能证明随后几秒的可见性，第 17 天居中请求还因持续滚动收到 `state_changed`。失败视频、请求和截图均保留；续录采用停放鼠标与前后两次像素检查，不能把首轮第 17 天后的画面标为合格。

补拍、剪辑与逐秒可见性复核见[第 1 集镜头台账](../../promo/ck3_native_war_ai/episode-01-battle-win-probability/camera-follow-footage-ledger.md)：266.4 秒净片的 267/267 个逐秒抽样帧均有中央战斗标记。此结果只证明该样本的拍摄视角，没有替整个游玩智能体长期运行或其他分辨率签核。

镜头跟随只处理“哪里是当前值得看的位置”和“画面是否朝向该处”。它不推断交战双方伤亡、事件概率、胜负或撤退，也不能把独立重放的数值轨迹拼成原始战役。战争模型和视频叙述仍依照各自的原生证据门禁。
