# E2-06/07 d11：R0107 RED 后新 attempt 准入

此计划在 2026-09-29 仅作无屏准备，**不授权启动 CK3 或录制**。R0107 原件与精确失败边界见 [R0107 RED 回执](e2-06-d11-recap-r0107-red-20260929.md)。屏幕队列先为 H3937 P0，再为 E2-04 d06 V3/trait/Regiment 61，之后才是 d11。任何新高优先级 WAR 请求继续由任务总线与主协调者安排。

## 修复组件，不改旧 run

R0107 的同帧 snapshot 可用，但 `ck3_query_battle_control_snapshot_v1` 因 `active_combat_resume_inputs_v1.observed` 模式拒绝。静态对照指向旧 join DLL producer 未发出两侧 `selected_commander_next_roll_bounds`，而 `#451` Python validator 已要求。不能对 R0107 重发查询、热换 DLL、补写 control、标正式 raw 或推断战斗成员集合。

1. 等原生项目从包含 `battle_control_snapshot_v1_mailbox.cpp` 两侧 next-roll-bounds 的**当前源码**构建一个全新正式候选。收 build report、绝对 DLL 路径、bytes/SHA-256、paired injector 路径/bytes/SHA-256、源 commit、原生 fixture 与 binary marker 审查。部分失败 build 保持 RED，不得作 run 输入。新 DLL/validator 语义和模式一致性须由独立代码审阅与测试证明；静态匹配仍不等于新实机响应。
2. 冻结当时 `#451` 精确 HEAD 与 `capture_session.py`、`remaining_live_step.py`、`pursuit_live_step.py` SHA；因 `remaining_live_step.TRACKS['e2-06-d11']` 目前固定旧 DLL/injector SHA，若新 pair 变化，先最小更新两个 pins、真实 source fixture 和负例，再独审并让 CI/CLA GREEN。不能用临时脚本绕过 `bind_session`，也不能为了过门放宽 battle-control 字段或 revision/snapshot_id 门。
3. 新工具链任务开始前再查最新正式 GitHub Release、wheel SHA、相对/主 venv 解释器、`xar_promo --version` 和相关 CLI `--help`；如有新正式版，先依 AGENTS 同步并升级。新 ProjectConfig run 在独立外置目录记录实际版本、配置快照和 source HEAD，旧 `e2-06-d11-recap-live-xar-run-20260929-a01` 不改写。

## 新无启动配对与屏幕门

- 仍以原 attempt-004 的 d11 save 52,408,560 B / SHA-256 `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953` 和真实 sidecar 13,397 B / SHA-256 `DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5` 为候选，actor 29829/date_raw 53146488/source run `native-29829-7ea6523df43e`。实际新 attempt 仍逐字节重验；源字节改变或 pair 不匹配直接 RED。
- 原生 A04 UI 100% 保存快照 SHA-256 `E6AD4D44435F17B77C6A5BD6554AB812FBF396D9A27370DB7CF9B56D658FDF7D` 与保全回执 SHA-256 `69F4535E4FDA428E910CBE6F3B44C70E352853535A2D546CB71AA09CEA941779`；54 B block SHA-256 `F5172E8A9DC92E8998957B5F443575608D04AC44342CE085DF23370CDA26F593`。新 profile 的 before-native、warmup后/final前、postmap/posthold 都必须实际读回原生 `value="1"`，全尺寸原图还要证实要拍的战斗下栏文字完整。R0107 只有磁盘 GUI 门，不能当下一次画面证明。
- 无启动预检必须用**新**外置 state/output/pipe，核 source、EXE、新 DLL/injector、UI 源、命令、进程空与 `ck3_started=false`，原件和 RED 回执 append-only。因 `capture_session.py --capture` 会独占创建 output-dir，静态 no-launch 所建目录不能再用于 live；正式 live 要另取全新根，在同一次 `--capture` 调用内先 preflight 后启动。
- 仅 H3937 与 E2-04 清场、根协调者正式排屏后，另领长期 heartbeat `ck3-screen:acquired`，确认零 CK3/FFmpeg/OBS，取当次新鲜 Steam 离线原图并本人直接审阅；如切显示模式，先核原生列出的模式、切换后重做截图新鲜性/桌面几何与离线门。受管结束恢复原显示。旧 challenge PNG、状态栏时钟、任务总线 ACK 均不能替代新图。

## 唯一新 d11 实机的停止边界

冷载后先核精确源 readback、paused/date/actor/War4/Combat16777218/Army18 与 GUI 磁盘门；原始 2560×1440 或当次实际尺寸截图必须见到所主张的战斗人数、下栏逐团/战宽控件、相机/地图和无遮挡 HUD。随后执行**唯一**新 run 的 `remaining_live_step observe`：snapshot 与 battle-control 的 wrapper revision、native revision、snapshot_id、成员集合都须同帧 GREEN。若复现 R0107 malformed/timeout 或内容不全，零正式 raw、零日期推进，保全 RED、受管清场和 RELEASE。

全部门通过后才开一个新 600 秒原速 FFmpeg raw，核首帧/几何、在 recorder 活跃且 d11 仍暂停时落 `d11-before` mark，绑定同 run control/report/原图原字节。只在剩余录制窗口足以覆盖动作和 d12 原图时，使用已审 helper 恰好推进 d11→d12 一次，落同 run `d12-after` mark；若窗口不足，封口为仅前态，不在 FFmpeg 停止后补日期并冒充同段转场。原生结果以新 run 数值重算；旧 J-A01/R0107/085 的数字只能作独立历史研究板。受管清场、显示恢复与租约释放后再审原片完整 PTS、内容和人工 1×，无人工签核前仍 `ENCODED_UNREVIEWED`、clean span 0 秒。
