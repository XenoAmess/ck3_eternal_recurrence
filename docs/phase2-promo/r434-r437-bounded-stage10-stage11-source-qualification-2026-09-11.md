# R434–R437：Stage 10/11 有界 source 资格核对

日期：2026-09-11

状态：**R434/R435 资格查询 GREEN，但目标门未满足；R437 为零游戏日 source-boundary RED；P1 仍为 `6/9 = 66.7%`，P2 仍为 `LOCKED`**。

本批遵循“小化改动匹配小化验证、单个 bug 不做永久长跑”的现行规则。三次 gameplay session 都只回答一个预先声明的问题；没有把未满足的结果改成延长观察窗或同形重试。

## R434：Stage 10 manager source 资格

R434 从 R432 checkpoint 启动，只调用一次
`query-zhongguo-manager-subordinate-selector-v1`，游戏日期在查询前后均为
`54487200`。查询返回：

- `status=unavailable`
- `selector_kind=zg361-bounded-ai-direct-manager-selection-v1`
- `provider_observed=false`
- `unavailable_reason=no_bounded_ai_direct_manager`
- manager/subordinate 均为 `null`

因此该 checkpoint 不存在可供 `.120` 使用的合格 AI manager/direct subordinate 对。R434 只完成了 source 资格判定，`stage10_gate_satisfied=false`；这不是 Stage 10 产品 RED，也不授权在同一 checkpoint 上继续等候。

## R435：Stage 11 terminal 零游戏日查询

R435 从同一 R432 checkpoint 启动，只调用一次 owner-view Workforce provider。查询前后日期同为 `54487200`，返回：

- `status=unavailable`
- `readiness.ready=false`
- `terminal=false`
- `terminal_kind=none`
- `unavailable_reason=subject_projection_read_failed`

因此该 checkpoint 不能直接提供 Stage 11 terminal，`stage11_gate_satisfied=false`。查询没有推进时间，也没有发送玩法输入；同一 checkpoint 不再为 Stage 11 重跑。

## R437：纠正 R398 source 边界误读

离线比对确认 R398 所加载产品中所有按 Workforce/Stage11/Central 相关路径筛出的 257 个文件，与当前 R430 候选逐字节一致。这个结果只证明旧实机中的相关产品实现可与当前候选比较，**不证明 R398 的输入存档已停在 `.242`**。

R437 no-launch preflight 为 GREEN，声明最多 30 个游戏日、禁止重试、只接受真实
`.242 → .360/独立 terminal`。实机载入后，初始 paused snapshot 为：

- player `32904`
- `date_raw=53611200`
- `active_event=null`
- `actual_advance_days=0`

operator 在入口身份检查立即停止，原因是 `current paused frame has no zg361we.242 event`。没有推进游戏时间、没有选择事件、没有查询或提交 `.360`，随后完成 managed cleanup。由 R398 历史记录可知，它是从该存档继续约 189 个游戏日后才到达 `.242`；此前将其描述成“`.242` 首入 checkpoint”是错误的。

R437 是 source-boundary/harness RED，不是 mod 产品 RED。257 文件一致性不能把一个 pre-entry save 提升为 near-terminal save，也不能据此签收 Stage 11。

## 证据

| 轮次 | artifact | SHA-256 |
|---|---|---|
| R434 | `Z:\ck3_mod_rewrite\_runtime\p1-stage10-source-r434-20260911\live-artifacts\stage10-zero-advance-source-qualification.json` | `9ADDB2D82CB094FFE39C2C17A36949E1E7D47C3FB0A5FE1B44D3DA4DFC626625` |
| R434 | canonical cleanup | `1BEE071F5478420C9C45B019A3418C5284C30872150B4AFA61BE094404642281` |
| R435 | `Z:\ck3_mod_rewrite\_runtime\p1-stage11-status-r435-20260911\live-artifacts\stage11-zero-advance-terminal-query.json` | `402E91D16B8F815CB6C32E14D38069C577D47D087AA64E5A24E0632BA3A988CA` |
| R435 | canonical cleanup | `336B302BAA2719D4B0B15F7F9F7DB1692B924BE32D6950A0E62E5D74E301F14A` |
| R437 | no-launch preflight | `A7DBC8C68C18B5312903789B964F0280A0BAA00724C1F170CA05D0B67AA10467` |
| R437 | `Z:\ck3_mod_rewrite\_runtime\p1-stage11-terminal-r437-20260911\live-artifacts\stage11-bounded-terminal-live.json` | `B1F8A8038A1D6456A234F39048331FAAA620E4A0560CC2659D19C4D2C5EE4C11` |
| R437 | canonical cleanup | `341A333C0C829B810D0C7CB0E33B197B5937F1F7F0B1447C2758531B9052EECC` |
| R437 | operator cleanup | `1932156F8F7E2C6246F049C0DC9A9C413064D3160E9A09A8FCFF2F16AC80D43F` |

R434、R435 与 R437 清理后的 CK3/injector inventory 均为空。全部 runtime operator、profile 和 artifact 均在仓库外 `_runtime`，没有修改 mod 产品树。

## 后续施工边界

Stage 10 下一步只接受离线可证明包含合格 AI manager/direct subordinate 的真实 checkpoint，或由既有 manager seed 路径生成并在同轮保存的 checkpoint。不得再对 R432 checkpoint 查询或长等 `.120`。

Stage 11 下一步只接受以下输入之一：

1. 真正在 `.242`、`.360` 或 owner-view terminal 附近保存的真实 checkpoint；
2. 在另一个有独立产品价值的有界流程自然到达该边界时即时保存的 checkpoint。

不得从 `date_raw=53611200` 的 R398 输入重新执行约 189 日单项长跑，也不得复用 R414–R418 已经证明主要消耗在 Stage 9/随机原版事件上的多次 continuation。找到合格 source 前，Stage 10、Stage 11 和依赖终态的 cold restore 都保持 PENDING。
