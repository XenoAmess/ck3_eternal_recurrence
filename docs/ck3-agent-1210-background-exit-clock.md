# CK3 1.21 后台正常退出与 Full 时钟接线

机器：`machine_id: 4-8e1c2f1861`；2026-11-18。目标是 CK3 1.21.0 Florin／build 26622941，EXE SHA-256 `2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC`。

本文记录源码与软件验收。未启动、注入、恢复、置顶或操作游戏；实机由 Root 独占，以下通过不代表实际游戏已经退出、推进日期或保存。

## 正常退出

既有 `normal_exit_map_driver_v1` 按真实 HELLO 选择明确的 `application_core_1210` 路由，通过已有单一 Native endpoint 发送 `normal-exit-application-v1`。它使用已资格的 Core ApplicationExit；不修改旧 GUI profile 的 SHA，也不把 Core 请求描述成菜单按钮、确认框或自动保存复选框操作。

正常退出仍要求当前 Full 与 HELLO 的版本、EXE、adapter、backend、PID、connection、public/native revision、signed character ID、日期及分配场次来源匹配。SDK 在派发前持久化原请求、原期限及 PID＋原进程创建时间的 create-only once claim。Native 也保留进程生命周期内的 ApplicationExit claim。

只有原请求的真实 `requested`＋`effect_attempted` ACK，以及派发前保留的同一进程句柄后续独立 signaled／exit code 0，才能产生 typed normal exit。缺失、错误或不确定 ACK 即使随后观察到 OS0，仍只有进程退出事实，原动作保持 UNKNOWN、不可重发。未结束的原句柄交给既有 `normal_exit_pending_observer_v1`；后续只读观察不重新打开 PID，不查询已经退出的游戏，不发送第二个退出请求。

共同验收客户端直接执行 query→confirm，再按需 observe；Core 路由不执行旧 GUI prepare／autosave toggle。最终 evidence join 仍校验冻结 source-index、SDK 三叶实际 SHA、allocated profile／inventory、原请求、once claim、SDK fsync 的事实收据及原句柄关闭收据。`autosave_disabled=null`、`autosave_verified=false` 明确保留；还必须由原 managed supervisor 独立证明 native0、清理与最终关场。

## Full 时钟与日期哨兵

`NativeHeadlessGameplayDriver._execute_primitive_step` 依据真实 Full 构造八字段 `full_snapshot_clock_control` 或 `date_sentinel_arm` claim，保留原请求 deadline，不接受调用方替换 Native 绑定。旧版本请求保持原路由。

1.21 Native 当前 Full-clock 入口要求 paused、map-ready、living player 的 Full；Python 不放宽成 running Full。Date ARM 进一步要求实际 war／army 列表为空，只接受 canonical `...-mode-terminal-a-0`，SDK 限定 1..31 整游戏日，起始日期与速度必须匹配当前 Full。

`resume-map` 必须先取得同 PID、scope、connection、起始日期与速度的真实 Date ARM ACK，并独立读取当前哨兵 status，核对原 generation 与完整 armed 状态，再重验 Full。ARM 许可在恢复请求首次可能写入前消费；不能发送裸 resume，重连也不继承旧进程内 ARM 许可。

既有 exact-day speed preparation 增加真实 Florin Full 的二次读取路径。当前已是目标速度时只记 `already_observed`、`submitted=false`、`accepted=null` 的观察证据；不发送冗余 setter，避免 Native `already_satisfied` ACK 被错当成可继续的提交。角色 ID 保留实际 signed full ID；前后速度或任一 Full 来源变化则停止。

Full-clock ACK 采用当前 C++ producer 的封闭字段与 exact-build/status/error 组合校验。`submitted` 仅表示队列／入口收据，不证明日期推进或物理保存。SAVE 额外保留真实 sequence、固定 `xar_checkpoint`、原 Full 日期；物理 savedPair 仍由既有保存验证器证明。`indeterminate`、已尝试后拒绝、`already_satisfied` 或缺失／畸形 ACK 保持 UNKNOWN。

持久路径为 `world-control1210/<pid>-<scope-sha256>/`。派发前记录 create-only claim 与实际 packet，收到的原始结果先独立保存。只有校验通过的原 ACK 才生成对应 qualification 收据；任何未 qualification 的 claim 都阻断同一世界后续 mutation，跨 public/native revision 和 connection 保留。只读查询与正常退出观察继续可用。事件／GUI 消费者复用本模块的 `require_florin_control_ready_v1` 与 `mark_florin_control_unknown_v1`，保留各自原 occurrence／widget claim，不借新 action ID 重试。

## 软件验收

- 既有正常退出合同、SDK→service→public wire、注册 MCP、原句柄观察、旧 GUI preparation／autosave 及新增 Core producer 链：74 tests PASS。
- 共同验收客户端 normal_close：24 tests PASS，包含两种 Core immutable evidence join；原 OS0、native0、finish_hold 与清理要求保留。
- 公共 normal-exit CI 的完整 strict 命令：3 source files PASS；共同客户端修改函数及 Core 合同全部新函数的实际 AST strict 范围 PASS。历史 `normal_exit_contract_v1` 整模块另有未迁移的旧泛型／import／旧 normalizer 类型问题，未报告其整模块 strict 通过。
- Full-clock／Date ARM、同速度观察及旧 timeline ACK：21 tests PASS；`timeline_control_ack_v1` 整模块与新速度观察完整函数范围 mypy strict PASS。夹具取自实际 C++ serializer 输出，transport correlation／世界输入为明确的无 CK3 软件夹具。
- 旧 exact-day 同速度、速度五与 paused-next-frame 行为：14 tests PASS。
- 本机真实安装数据的离线 profile 测试：6 tests PASS／14.723 秒，包含 `XAR_CK3_1210_OFFLINE_METADATA_GAME_DIR` 显式指定真实 1.21 安装根后的 metadata builder→公共 static binding→原 host argv→未 mock 的 inventory／running-input verifier→Core Driver/service→共同客户端 immutable evidence join。使用当前金融产品实际 GUI 与原版依赖，未启动 Game；未提供安装根的 CI 明确 skip 该实机文件测试。

增量测试复用仓库 `tools/.venv/Scripts/python.exe`；未新建服务、pipe 或 Native worker。CI 复用现有 `static-ci.yml` 步骤，不以软件绿替代实机资格。

公共准备不需要新 profile 类型：`allocate_normal_exit_profile_v1` 在本场次 `live/normal-exit-binding/` 调用现有 `create_profile`，生成 `normal-exit-managed-profile.json`，原 `--normal-exit-managed-profile` 与 `--normal-exit-managed-profile-sha256` 负责 host 绑定。此 builder 从实际 EXE、stock GUI、产品完整文件集生成 inventory；不调用旧 GUI ABI contract 生成器，不授予旧 GUI Native 按钮执行能力。Core 路由额外核对 profile 的版本与 guard EXE SHA 等于真实 Florin，随后仍要验证实际文件字节及独立 Full／HELLO。
