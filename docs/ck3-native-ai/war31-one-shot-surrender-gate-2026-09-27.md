# WAR31 守方投降：单次受管 typed action 门禁（2026-09-27）

本工具只为 [R0221 精确请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json)的独立实机验收开放。项目所有者在本轮聊天中对**匹配检查点**明确回复“授权这一次匹配检查点的投降动作”。较早请求中的“不授权”并未被改写；它是历史事实。本页是**离线实现和操作合同**，不表示投降已经执行，也不表示材料后果已经确认。

## 硬门禁

默认 `NativeHeadlessGameplayDriver` 完全不启用 WAR31 例外。操作进程必须显式提供一个 `War31OneShotSurrenderGate`：它在创建时核对外部授权回执的精确字段、R0197 原始 `xar_checkpoint.ck3` SHA-256 `1AF4055F978AF60267FB3A0D8658224047CD6BFDA884C66886A13B74EE34A90A`、原始 `driver-state.json` SHA-256 `1DE61CF0AC47EDD1D63FE1F3D77668D5F499EA6CA06B90BC83B068CF35F16336`。派生 rebind driver 不拿来冒充原始 driver。

唯一可投递的动作是 `surrender-war-16777231`，且每次能力展示及提交前都要同时匹配：Robert `29829`、episode `native-29829-2bc2d599f7f9`、`date_raw=53215920`、WarID `16777231`、守方主战争领袖、对手 `30097`、目标 title `[2128]`、战争分数 `-15`，以及相同暂停原生帧中的 fresh `query-war-termination-options-16777231`。原生查询必须报告 de-jure CB `17/individual_county_de_jure_cb`、战事时长 `1045` 天，**守方投降结果 `attacker_victory`**，原生 validator/可用性/自动接受/接收方现在接受均为 true。任何字段、帧修订、连接 generation、episode 或日期不一致都会拒绝。此例外没有修改一般进攻方紧急投降策略。

调用原生动作**之前**，门禁在授权回执所在目录使用独占创建并 `fsync` `war31-one-shot-submission-reservation.json`。该标记一旦存在，当前进程及重新启动的进程都不再展示或执行动作；即使原生 ACK、游戏后置或 Python 进程失败，也不自动重试。授权回执应放在跨 attempt 共用的固定外部目录，不能为新 attempt 复制出另一份回执和标记来重置单次授权。标记是“尝试即消费”的记录，不能当作游戏接受或完成的证明。

## 接入顺序

1. 在**外置、跨 attempt 固定目录**写一份人工转录本轮用户授权的 UTF-8 JSON 回执。字段必须精确为：

   ```json
   {
     "schema": "xar.ck3.war31-one-shot-user-authorization/v1",
     "request_id": "WAR-INPUT-R0221-WAR31-20260927",
     "action_step": "surrender-war-16777231",
     "source_checkpoint_sha256": "1AF4055F978AF60267FB3A0D8658224047CD6BFDA884C66886A13B74EE34A90A",
     "source_driver_sha256": "1DE61CF0AC47EDD1D63FE1F3D77668D5F499EA6CA06B90BC83B068CF35F16336",
     "episode_run_id": "native-29829-2bc2d599f7f9",
     "date_raw": 53215920,
     "authorization_text": "授权这一次匹配检查点的投降动作",
     "scope": "one matching checkpoint surrender action only"
   }
   ```

   这是操作员对聊天授权的转录，**不能仅凭代码自报当作新的用户授权**。原文件与回执的 SHA、路径、来源、操作者和时间应写入本次 attempt 的外置 manifest。新 run 必须由原始四文件完整 prepare/rebind 和 no-launch preflight；任何已有 attempt 的派生 state 不得覆盖。当前已有的 attempt-01 若与新代码运行路径不能经只读预检证明配对，就新建 attempt-02，不在原目录重新准备。

2. `native-session` 是 CK3 进程监督器，并不处理 `ck3_execute_step`。对准备好的 `xar_off` profile，显式以 `xar-autoplayer --state-dir <prepared-state> --bridge-mode native-headless --bridge-pipe <exact-pipe> native-session --cold-start-checkpoint --xar-enabled xar_off` 启动。先走既有同轮排他锁、Steam 离线新鲜画面、原版 DLL/EXE 哈希、sidecar 和 no-launch 门禁。`--xar-enabled xar_off` 只选择已有 profile 的预期状态，不修复或重写它。

3. 与同一 state/pipe 连接的 **MCP stdio 进程**必须显式采用 `native-headless`，并一次性传入四个参数：`--war31-one-shot-authorization-receipt <固定回执>`、`--war31-one-shot-source-checkpoint <原始R0197存档>`、`--war31-one-shot-source-driver <原始R0197驱动>`、`--war31-one-shot-submission-fence <回执目录/war31-one-shot-submission-reservation.json>`。四项缺一、其他 driver 或非 stdio 均拒绝。该 MCP 进程的 `NativeHeadlessGameplayDriver` 在构造时注入门禁；启动后的独立 `native-session` 监督器没有可动态改写的动作门禁。若 MCP 进程已先以无门禁版本启动，必须停掉该 MCP 进程后用同一受管 state/pipe 重启并重新做只读配对核验，不能声称它已热加载新代码。

4. 暂停并核对 exact episode/date/角色/WarID 后，通过 typed `ck3_execute_step` 先发 `query-war-termination-options-16777231`，保存原始查询及当前 snapshot/能力字节；只在本帧出现唯一 `surrender-war-16777231` 字面 action 时，执行**一次**该动作。保存原始 ACK、driver history、一次性标记和紧邻暂停快照。结果中的 `war_termination_result.outcome` 必须是 `attacker_victory`。ACK 若仍显示 `submitted_pending`，不得称战争已结束。

5. 以独立读者验收战争结果、title/holder/liege、资源和停战；必要时按既有受管流程推进下一 turn、保存检查点、冷恢复并复读。将未知与零变化分开记录。后置、下一 turn 和恢复任一未证明，WAR31 仍为 RED。硬件双点观察若另行执行，保留原始 trace 和调试器扰动边界；它不替代游戏后置。

本次离线验证：`test_war31_one_shot_surrender.py` 五项 GREEN，包括守方 `attacker_victory` 的 FakeEndpoint typed 路径、同帧失配拒绝、文件哈希拒绝、标记持久拒绝及 CLI 参数解析。尚无 WAR31 实机动作证据。
