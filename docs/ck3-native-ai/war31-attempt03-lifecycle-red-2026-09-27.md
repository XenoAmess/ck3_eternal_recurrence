# WAR31 attempt-03 只读连接 RED 与运行时修复

Robert h2577 窗口正式释放后，本机从已校验的四份 R0197/R0221 原件另建 `D:/ck3-research-artifacts/war31-live-20260927/attempt-03`；显式原管道的 no-launch preflight 为 READY。Steam 保持离线；进程和启动记录确认没有其他 CK3 会话。使用原 R0221 DLL 和精确 R0197 检查点冷启动，游戏 PID 17436。

MCP 的首次**只读** `ck3_take_snapshot` 在驱动接管时失败：CLI 默认按 `rogue_one_life/xar_on` 构造驱动，而这次重绑的 R0197 状态明确是 `ordinary_campaign_succession/xar_off`。既有的接管校验拒绝了不同的冻结生命周期。因此该 attempt 没有查询或执行投降；跨 attempt 的单次提交 fence 不存在。启动监督器随后受控停止游戏并确认进程树消失。失败响应和日志保留在外置 `attempt-03/live-mcp-controller` 与 `attempt-03/native-session`，不能改写为 GREEN。

修复是在 MCP native-headless 入口新增显式 `--environment-manifest`、`--succession-lifecycle`、`--ordinary-campaign-no-pact`，通过既有 prepared-environment binder 构造生命周期绑定并交给 native driver。驱动接管仍要求其与持久状态完全相等；ordinary no-pact 与 `xar_off` 必须显式同时成立。WAR31 controller 同时保存每次 MCP 响应的原始 envelope 和独立 structured payload，便于战后读数复核。`attempt-03` 保持 RED；下一次实机必须从原件建立新的 attempt。
