# CK3 1.20.0.2 AI reform inputs owning caller fixture

2026-10-01：一个新组合只读场景，**两次 actual queued commands / 12 checks**，首次 `/O2 /W4 /WX` GREEN。真实 owning caller 完成 `TrySubmit → owner Drain → actual Core/resolved played actor → holder context → each controller schedule → Finish → Wait/Reclaim → complete command_result`。exact-build 为 1.20.0.2，EXE SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。

此工作只消费冻结[AI context 原生树与 ABI](religion-reform12002-ai-context.md)和[schedule 原生树与 ABI](religion-reform12002-schedule.md)。旧 AI context 9 cases、schedule 8 cases 及 query 12 cases 均未再次运行。fixture 只包含冻结 query 的 memory/owner helpers，将旧 `main` 重命名；实际 controller 来自当前 holder，不使用 default context 代替真实成员，不预测优先级、调用 scheduler 或执行改革。

## 同一场景的两次实际观测

第一次 command 的 holder table 有五项：ordinary A、player-special、ordinary B、另一 actor 的 controller、default。实际 reader 保持顺序返回前三项，不为任何成员猜测优先级。逐项消费真实 `actual_ai`：ordinary A 的负 countdown 为 **-4**、selected 为 1；special 无 extension，`gates_only` 且 timer unavailable；ordinary B 的 active 为 0，正 countdown 为 **12**。独立 per-member schedule 分别为 `observed/gates_only/observed`。

第二次 command 只保留 nonactor 与 default 两项。reader 返回合法 `observed_no_ai`、零 controllers、`controller_absence=no_actual_controller`。基础 schedule 在两次 command 都实际读取 native globals/current actor，保留原 `ai_status=not_supplied`；所有 AI cache 与 timer 值为 `null`，不是伪造的 false 或零。当前 independent=false、reformation toggle=false 均为有效观察；highest tier=2、rare period=360。所有计时单位保持 `prepare_invocations`，不声称是天数。

actor=50331652、date_raw=53175816、published snapshot_revision=701。两次独立 owning pump 的 capture epoch 均为实际 epoch **3**。actor 参数身份检查通过，tier/independent getter 总调用次数为 5/5。每次 capture 后 actual holder、controller、extension、collection 均与 capture 前逐字节相同。

## 实际协议与证据

完整协议直接由 C++ production caller 序列化，Python 仅解析验证，没有补写 DTO 或 metadata：

- `type=command_result`、`protocol_version=1`、`ok=true`、`status=observed`。
- `step=query-player-religion-ai-reform-inputs-v1`、`domain_key=player_religion_ai_reform_inputs_v1`。
- `backend_id=ck3-1.20.0.2-native-player-religion-ai-reform-inputs-v1`。
- `result.player_religion_ai_reform_inputs` 使用 schema `ck3_12002_player_religion_ai_reform_inputs_v1`，嵌套 context 使用冻结实际 serializer。
- 两个 whole packet 均无 internal `actual_ai`、pointer、address；controller 只发布 typed kind/raw/state/schedule。

结果：`Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\ai-inputs-caller\attempt-001\result.json`，SHA-256 `09d527ccb679eded5411655eaacd3648e138eb9a6e72bf2c89b60bb732098aa7`。

两份 raw complete packet 为同目录 `wire/multiple-controllers.json` 与 `wire/observed-no-ai.json`。精确 packet hash、所有编译输入与缓存对象 hash 在 receipt；新三份 owned sources 的路径与 hash 在 `ai-inputs-caller/final-source-package.json`。Python SDK owner 已收到两份原始 packet，将在同一新增 cache → wait → query unit 中消费。

新 production define 为 `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1=1`，新 production 源为 `religion_reform12002_ai_inputs_mailbox.cpp`。fixture-only define 为 `XAR_REFORM_MAILBOX_STANDALONE_ADAPTER=1`。当前 shared mainthread/query envelope 两源重新编译；AI context、schedule 与其他 production 库复用冻结 O2 objects。没有 shared 源、CMake 或 provider 修改。

## Readiness

这是 **static-ready readonly combined AI input query wrapper**。`gate_inputs_observation_complete=true` 只表示本帧所需输入观察已完成，合法 no-AI 同样为 true；不表示 AI 将改革、reform 合法性、未来发生时间或动作成功。

fixture 使用 actual generic `permitted_executor` exact callback，新专用 `permitted_executor_religion_ai_reform_inputs12002` 尚未在本包注册或验证。下一步由 central 接 dedicated slot，再执行独立单 named case；root 负责 paused live。此包没有 CK3、pipe、UI、Steam、战争研究、Git 或 live 声明。日/周字段随 `ai-inputs-caller/report-fields.md` 交协调者合入，Git commit/push 由 root collector 执行。
