# R300–R303 credit project 恢复与 projects/metrics MCP 实机闭环（2026-09-08）

## 结论

R303 已在 CK3 1.19.0.6 的真实暂停现场完成 credit project 收口、原生 MCP 换人和 projects/metrics action cell 的连续闭环，最终结果为 `GREEN`。MCP 在 owner 仍为当前玩家时直接读取 subject 的 portfolio 终态，随后由 native `set-player-character-v1` 在同一暂停帧把玩家从 `32904` 切换为 `30938`，再执行一次 `life-advance`，最终取得与同一项目身份绑定的 metrics 回执。

这轮解决了 R300 暴露的存档恢复缺陷，也移除了旧 UI key `.133` 对项目收口的错误依赖；但该 MCP 仍是 `private candidate / default off`，而且本轮没有生成 canonical `capture_projects_metrics` schema-2 source checkpoint。因此 source registry 仍为 `1/4`，T0-P1 与 T0-P2 均未被本轮解锁。

## R300：save/load 后 delayed player event 丢失

- R300 从 credit project `.26` 后的真实 checkpoint 恢复时，发现 save/load 会丢失尚未投递的 delayed player event。
- 结果是业务状态已经向后推进，但恢复链无法可靠重新投递精确的玩家事件；继续依赖 UI/event 表象会把真实业务进度误判为停滞。
- 该轮保留为产品 liveness RED，修复目标被收敛为：把待投递状态 durable 化，在 load/resume 时按保存的 owner、subject、cycle 与 cursor 重建精确作用域并继续分发。

## R301：durable cursor 修复 live，通过 `.134`

- 修复后的恢复链能够从同一 `.26` checkpoint 继续推进，实机依次经过 `.31`、`.57`、`.62`、`.131` 与 `.134`，portfolio finalizer 已真实执行。
- 旧 orchestration 仍等待 UI key `.133`，因而把已经收口的 portfolio 误判为未完成。debug ledger 证明问题位于验收 gate，而不是 credit project finalizer。
- 本轮结论是：`.133` 不是可靠的业务终态信号；后续验收必须读取 owner/subject 上的 durable portfolio closure 与 conservation 状态。

## R302：首次 explicit-subject MCP closure 与换人成功

- 新的 projects/metrics MCP 已能在当前玩家仍为 owner `32904` 时，以显式 subject `30938` 读取项目终态。
- portfolio closure 与 native MCP 换人均在真实暂停现场成功；换人后 date 未漂移，postcondition 得到验证。
- action-cell preflight 因 caller 没有继续传递 `subject_character_id` 而 RED。该失败是调用方接线错误，不是 CK3 产品状态或 MCP provider 的 capability RED。

## R303：完整业务后置条件 GREEN

### 冻结输入与实机身份

- source checkpoint：`Z:\ck3_mod_rewrite\_runtime\p2r301cp26cursor_state\profile\save games\xar_checkpoint.ck3`
- checkpoint 大小：`89,563,632` bytes
- checkpoint SHA-256：`7584F32E1D3556A7740FE1E11FA5AF67706A47C99A25E52E1E69213673D15870`
- owner / subject：`32904 / 30938`
- closure paused date raw：`53247312`
- cycle / final case / final state：`4 / 2 / 6`
- final conservation：`1`
- pending player event：变量不存在，按合同解释为已清空

R303 前后重新核对 source checkpoint，大小和 SHA-256 均未改变；原始恢复证据没有被测试过程覆盖。

### MCP closure、换人和 action cell

- explicit-subject provider 在 owner 仍为当前玩家时返回 `portfolio_observed=true`、`portfolio_closed=true`。
- native `set-player-character-v1` 从 `32904` 切换到 `30938`，保持同一暂停 date raw `53247312`；`postcondition_verified=true`、`episode_rebind_performed=true`。
- action cell preflight 为 `READY`；随后只执行一次 `life-advance`，不使用 OCR、坐标或视觉 fallback。
- projects/metrics 业务后置条件为 GREEN：身份 `[32904, 30938, 4, 2]`，contribution receipt id `1`、revision `3`、value `1`，metrics revision `2`，dictionary `metric_dictionary_subject_v1`。
- terminal reason 为同一 `.26` receipt 已被 committed P3 metrics result 消费；action ACK 没有被冒充为业务完成证据。

### Artifact 与清理

- report：`Z:\ck3_mod_rewrite\_runtime\p2r303projectsmetrics\report.json`
- report SHA-256：`926BBD25076F69205B8AAA7CCC366AB470227BCBE174017B7E86C282862D7B01`
- report result：`GREEN`
- cleanup result：`GREEN`，failed checks 为空；最终 CK3/injector 进程槽为空。

## Readiness 与进度边界

- 本轮实机证明的是 private-candidate provider、native 换人和 action cell 能闭合一个真实 projects/metrics 业务后置条件；provider 仍为 default-OFF，不能写成默认生产能力。
- canonical source registry 仍为 `1/4`：promotion/compensation 已有 schema-2 capture；projects/metrics 尚未创建对应的 schema-2 source checkpoint，incidents/operations 与 cross-cycle/endgame 也仍缺失。
- 本轮是跨域业务闭环与采样管线证明，不新增已枚举的 strict business scene，也不完成新的 full-tree stage。
- 进度保持：T0 `50%`，strict scene `4/361`，full-tree definition `106/626`，stage `8/11`；T1 `90%`。
- 宣传素材仍为 footage `0/8`、MP4 `0/2`；T0-P2 继续 `LOCKED`，未开始最终宣传视频制作。

下一工作包是复用 R303 已验证的 explicit-subject MCP 与 native 换人链，生成 `capture_projects_metrics` 的真实 paused schema-2 source checkpoint，并把 canonical source registry 从 `1/4` 推进到 `2/4`。
