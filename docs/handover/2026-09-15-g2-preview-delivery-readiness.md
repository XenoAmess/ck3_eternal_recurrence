# G2 可运行预览包交付门（2026-09-15）

本页只登记预览包的当前可用性。权威 G2 里程碑仍见
[`g2-requirements-v1.json`](../autonomous-agent-progress/g2-requirements-v1.json)：`1/8`，预览包不改变该分母或状态。

## 当前结论

截至本页核验，**还没有可以交给用户直接启动的预览包**。远端主仓 `master@c701a8ff5e8bacb8ccbf9e124553562986b4012e`
有正式 `native-auto-run` 与 `ck3_auto_turn` 入口，但缺少与当前源码、Release DLL、injector、production profile、
普通封建存档和实机断言共同冻结的交付制品。独立分支 `G2-PREVIEW-STOP` 已修复 Ctrl+C 不能确保已验证进度
落盘的 B0；合入后仍须实机验证冷恢复与同一目标接续。

| 最小门 | 当前证据 | 还缺什么 |
| --- | --- | --- |
| 普通 production 存档经正式策略运行 | R675 完成 `12/12` turn、四次 `NO_DECLARE` 日期推进与 checkpoint；旧制品 `44b6978` | 当前冻结制品上真实非空策略动作、独立后置状态、下一 turn 消费 |
| 可控停止和保存 | `G2-PREVIEW-STOP` 的 normal / `-O` 聚焦测试各 `63/63` GREEN；首个 Ctrl+C 延至完整 turn 边界保存，第二次为紧急中断 | 同版本 paused 实机保存、受管进程清理与停止报告 |
| cold restore 与目标接续 | 既有 native v2 checkpoint/driver-state 合同和历史实机冷恢复成立 | 新交付候选上新 PID/轮次恢复后继续原目标，先查 pending 动作，不重复生效动作 |
| 获取与启动说明 | 仓库入口 `ck3_autonomous_player/agent.py`，CK3 exact build `1.19.0.6` / EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` | 冻结包路径/SHA、实际测试过的完整命令、DLC/mod/load order、支持与未支持范围、证据索引 |

R675 保留的普通 campaign checkpoint 是
`Z:\ck3_mod_rewrite_process_assets\g2-m2-r675-campaign-44b6978\state\profile\save games\xar_checkpoint.ck3`；
同目录 `state\native-session\driver-state.json` 是恢复状态。R675 使用旧 runtime、旧 DLL 和旧 profile，不应与新源码
拼成一个声称已验证的用户包。R693 的 sealed candidate 只实证私有、paused、只读的 Council reader，没有正式动作或
下一 turn 消费；它也不能替代预览门。

## 下一场有界预览验收

在启动 CK3 **之前**，负责人固定新的主仓 commit、Release DLL 和 injector SHA、production profile manifest、普通
标准封建存档与其 driver-state、CK3 EXE/DLC/mod/load order、pipe、正式命令、turn 数与墙钟超时，并记录轮次和
唯一实例所有权。运行只用正式 `native-auto-run`，要求至少一个非空策略动作及独立游戏后置变化，下一 turn
消费这项变化；第一次 Ctrl+C 在完整 turn 后保存并清理旧实例；用同一 state/pipe/制品的
`--cold-start-checkpoint` 新建轮次，恢复后继续原高层目标且不重复已生效动作。RED、超时、未执行与证据不足分开
记账。通过后立即填入真实制品位置与校验信息，并给用户完整、已实测的启动/停止/恢复命令；此前不把占位示例
当成可执行交付。

Ctrl+C 补丁只增加正式 CLI 的停止请求和私有 `native-auto-run` 报告状态；公开 native/MCP capability、协议和
schema 没有变化，当前不需要 `open_kaishek` 适配。停止操作 `outcome=operator_stopped / ok=false`，与
`outcome=qualified` 明确分开；未确认动作、checkpoint 失败或 cleanup RED 仍保留失败报告。
