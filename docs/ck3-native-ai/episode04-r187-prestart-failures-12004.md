# E04 R187：两次开场前拒绝（1.20.0.4 目标）

R187 两轮都没有启动 CK3、SDK 游戏会话或录制，新增原片、完成游戏日、clean、业务正例与人工签收均为 0。它是开场诊断记录，不能占用 R03 或任何视频业务资格。动态视频资格仍 0/11；既有研究 6/14、业务 4/11 不因本次失败变化。

机器为 `desktop-3fevhd2-1c74096080`；源与复用 native 构建来源均为 `d05b0c780b615faa714fdf0535403bb2e6941faf`，目标版本为 1.20.0.4，本轮没有新的实际运行时版本/身份读回。场次目录为 `D:/workspace/ck3_native_war_ai_promo_work/e04-r187-window-capture-a01`，run ID 为 `desktop-3fevhd2-1c74096080--vanilla--R0187`。下列时间为 2026-10-16 UTC，即北京时间 2026-10-17 凌晨。

| 尝试 | 实际时间（UTC） | 拒绝点与实际结果 |
| --- | --- | --- |
| a01 | 17:38:03.795869–17:38:15.192567 | 子进程 exit 1。旧 army-history runtime capacity 解析器要求 `source.new_clean_integrated_source_head`；本轮容量记录使用 `source_binding`，虽 `admitted=true` 且顶层机器/来源匹配，仍在创建 run_dir / SDK 前抛出 `runtime capacity machine/source/admitted differs`。 |
| a02 | 17:48:31.262574–17:48:39.250379 | 去掉旧 `--runtime-capacity-admission` 参数，以同一源重试；run_dir 已创建，但 screen keeper 在孩子启动前拒绝过期 heartbeat，exit 1。`recorder.state=NOT_STARTED`、`capture_source=null`。 |

a01 的归档在 17:48:31.224489 明确记录 run_dir、identity 和 CK3 进程当时均不存在。原 relay 错误已复制进 a01 归档，不能把可能复用的 canonical relay 文件名当成 a02 错误归属。a02 的依据是独立 launch call、bootstrap result 和 keeper journal；`sdk_error=null` 仅表示没有 SDK 错误值，不证明 SDK 已连上。

a02 screen sequence 为 5817。保留的 acquire stdout 中 heartbeat 为 `17:29:22.210074+00:00`，keeper journal 拒绝时间为 `17:48:38.574131+00:00`，两者相差 **1156.364057 秒（19 分 16 秒）**，超过既有 `MAX_AGE_SECONDS=600`。sequence、任务状态和资源名正确不能替代 heartbeat 新鲜度；此处复述现有 keeper 行为，没有新增门禁。

原 `bootstrap-input.actual-a01.json` 的 `game_started=true` 是过早填写的错误意图，原件保留；两轮真实执行均为未启动。其 `identity=null` 和保留的 identity 输出路径，也不能证明已获得角色身份。准备的 a29 DLL 为 13,000,704 B / SHA-256 `e4f2b7200a0029a56d83904b627aff724fb654b6983753da4c66af9d4e06fbbf`，这是输入 pin，不能改称本轮实际加载。

对视频剪辑：本轮没有可用新镜头，不把它当成窗口捕获黑屏、截断或 CK3 崩溃，也不沿用 R186 正常结束来补本轮启动事实。对智能体开发：区分输入意图、进程退出、屏幕租约、SDK 会话、原生动作和录像结果；两次失败必须按尝试分别归因。Root 后续以独立 R188 恢复/新场次继续，本记录不追认 R188 成功或本机后来的 Steam/容量/权限状态。

便携证据见 [source-index.json](evidence/episode04-r0187-20261017/source-index.json)，包含 16 份 exact 小原件、完整外置来源路径与 SHA-256，以及四个源码的 HEAD/blob/SHA/CRC pin；[派生事实](evidence/episode04-r0187-20261017/facts.derived-a01.json)显式保留错误意图与实际状态的更正。关键 a01 错误 3091 B / SHA `ffa7d831acda9258a133f738e3328fe5d2de24b60414bef0051a2edf106e1040`；a02 bootstrap result 1163 B / SHA `b4ef695628a61f0f6e2e6fa2e655bf1d7206ca37c80c552e40794cdfb25fc381`；journal 188 B / SHA `dcf5417da050fe4b289ae54a056f739519d394aa47e2696d2d416ec11854e76d`。

本包只做小原件逐字节复制与清单/补丁封装，未重跑测试、未执行游戏/桌面/SDK、未更改运行源码。原片、截图、存档、二进制及完整依赖只保留已有外置 pin；其他机器必须重新核对自己的机器 ID 与实际状态。小型诊断记录按通用存储策略 1.0.0 的 record 周期复核，不授权永久保留所有外置准备材料。
