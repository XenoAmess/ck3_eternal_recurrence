# R497/R498 Stage 10 `stress_threshold.1011` RED 与合同补丁（2026-09-12）

## 当前结论

旧轮次 R497 已在当前轮次 R498 启动前终止。当前轮次 R498 / PID `37604` 是唯一 CK3 实例，仍暂停在
`date_raw=53155728` 的原版事件 `stress_threshold.1011`，instance `20`。Stage 10 从 source
`date_raw=53155680` 前进一天后已用既有合同关闭 `sway_outcome.1001`，再前进一天撞到本事件。选择没有提交，RED
保持；B1 仍 active，Central/PP 均 false，`.120` 尚未被评估。因此本 RED 是产品结果之前的未知原版事件中断，
不能写成 B1 通过或失败。

冻结 artifact 为：

- `Z:\ck3_mod_rewrite\_runtime\p1-stage10-player-publication-r497-r498-0aa1576-20260912\live-artifacts\stage10-player-subject-red.json`
- SHA-256：`B51B8960C470FA5D76A73724F6791425EF5B23BF4FC10B6D361DF4B6574F392F`
- source checkpoint：`65,244,992` bytes，SHA-256
  `27CDB78E042294096395CAF0A4ECBB4D361213391B0E4E97BE76B1C28417EA6C`
- exact build：CK3 `1.19.0.6`，EXE SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- native frame：snapshot `native:10`、native revision `10`、revision `11`、connection generation `1`

## exact-build 原版定义与调用链

权威事件定义位于 `events/stress_events/stress_threshold_events.txt:882-1281`，文件 SHA-256 为
`66538A8FE8C894A52D8EC89B2FC4A45B85B8D1B9464802263E45D582CE1CA42B`。一级压力阈值管理事件
`stress_threshold.0001` 在没有特殊死亡/禁欲冲突分支时调用 `stress_threshold_level_1_event`；
`common/on_action/stress_on_actions.txt:78-93` 的随机池以权重 `100` 包含 `.1011`，该文件 SHA-256 为
`35A9B8FC8FE6CDE91EAAD06F9C90AD6FCD41BEEFD317BFF77D3A68430E5DD839`。

`.1011` 的 immediate 保存 `stress_character`，并最多挑选两个 coping 路线。六个 authored option 分别为：

1. native `0`：添加 `rakish`，执行妓院效果；
2. native `1`：添加 `reclusive`，执行关系损伤；
3. native `2/3`：改变信仰并改变虔诚/压力；
4. native `4`：添加 `athletic` 并降低压力；
5. native `5`：无条件增加 `mental_break_opt_out_stress_gain`，随后进入共同阈值清理。

R498 的只读现场只有 native `0/1/5`，且三者均 shown/enabled。root 与 `stress_character` 都是玩家 `27181`；
`neglected_spouse=48337`，两个 scope 的原生类型均为 character。native `5` 是此现场的最小影响确定路线：它只改变
当前玩家压力，避免新增 coping trait、妓院的疾病/怀孕等后果、关系损伤和信仰变化。代价边界被明确保留：它会增加
压力，不能描述成无效果按钮；共同 after 仍由原版执行阈值清理与未来 cooldown 准备。

## 通用合同资产

共享 `xar_autoplayer.vanilla_events` 新增 campaign-neutral 合同：

- root 与 `stress_character` 使用 `$player`，不固化 R498 的 CharacterID 或日期；
- 精确要求两个 saved scope：`stress_character` 与 distinct typed `neglected_spouse`；
- 精确要求 snapshot authored count `6`、rendered native indices `(0,1,5)`；
- 选择 authored option `6` / native index `5`；
- occurrence 为 observation window 内可重复；
- analysis 保留 exact-build 定义、调用链、所有 authored option 的影响和选择理由；
- observation 保留 R498 的选择前 RED、现场身份、revision、bridge 与未尝试选择状态。

source index 已更新为 `185` 个唯一事件定义、`523` 条 lexical caller candidate；portable evidence 增加本 RED
artifact，变为 `282` 个 content-addressed blob。资产继续通过只读 MCP 查询复用，不依赖操作者、固定机器路径或当前轮次。

## 针对性验证与下一动作

仅运行本变更相关的六个 vanilla-event 测试文件：normal 与 optimized 均为 `59 passed, 82 subtests passed`；
source-index generator byte parity、portable evidence 离线自校验包含在该集合内。R498 冻结现场的离线合同回放为
`18/18` checks GREEN，解析结果严格选择 authored `6` / native `5`。首轮测试只发现一个证据总数旧期望 `281`，
修为 `282` 后同组通过，没有扩大整仓验收。

本包只改 Python 合同、测试、source index、portable evidence 与文档，不改 DLL、游戏文件、启动参数、加载顺序或
运行环境。提交、rebase、push 后按 SOP 在当前轮次 R498 原位热恢复；不得发送第二次 `run-stage10`，不得重启 CK3。
若热恢复遇到新的未知事件或产品 RED，继续保留首个新 RED 并停止。P1 仍为 `8/9`，P2 最终宣传视频继续
`LOCKED`。

## 托管超时与现场闭环

根仓 commit `6e780e08d136df8d8fb0141c8f0d41bab644fcf2` 与 open_kaishek commit
`1122d9f6c53b48660bde9e2ab54a8844bf76eef3` 均完成 rebase、push 与本地/远端一致性确认。提交和兼容同步期间，
R498 达到 activation 明确配置的 1200 秒运行上限；随后通过 canonical cleanup 取得完整 session report：

- 当前轮次 R498 started `2026-09-12T02:40:13.087724Z`，finished
  `2026-09-12T03:00:19.515267Z`，elapsed `1206.428s`；
- `exit_reason=timeout`，对应 activation 的 `runtime_timeout_seconds=1200`；
- gameplay PID `37604`，generation `1`，restart count `0`；
- shutdown 后 process tree 已消失，Job active processes `1 -> 0`，final CK3 inventory empty；
- canonical cleanup SHA-256 `A93FB075F6FB8E09664FCE2ACC8BB7BEA8B24CC3F2E0E56E435C785A0112DD7C`；
- managed cleanup SHA-256 `F90F824DAA83C5525B14C5162087FCC4B2D5FF46CB974F68013A2E33E72E03EB`；
- cleanup result `GREEN`，没有未解释的进程/资源 RED。

没有发送第二次 `run-stage10`，也没有把超时伪装为同进程恢复。当前轮次 R498 与旧轮次 R497 均已终止；
CK3、injector 和托管 Job 最终清空，因此原计划的同进程热恢复据实取消。下一次唯一允许的启动为 R499 warmup / R500 gameplay，
复用同一 source 与 120 游戏日绝对边界；不得扩大为永久长跑。
