# R179 B1 quota-bank close 后 calibration 回调停滞取证

日期：2026-09-07（Asia/Shanghai）
状态：`static-fixed / live-pending`
范围：天朝二期 promotion-source 的真实产品 B1 年度链；修复已完成生成器、生成结果与静态门闭合，尚未经过新 CK3 进程实机验证。

## 结论

R179 已把故障收窄到 B1 的 `common-superior bank close -> manager calibration`
接力缝：玩家经理完成事实冻结、本地 quota book 和 exact common-superior bank close 后，
仍未从 `zg361_b1_cycle_state = 6` 前进到 calibration，最终在完整产品时间线上持续保持
`B1=true / Central=false / PP=false`。

当前硬证据能够证明“接力缝未产生业务结果”，并支持“manager-rooted D+1
`zg361b1.111` 没有可靠落地”为最强解释。仅凭现有只读 GUI witness 和日志，不能把
以下两个更细分支绝对区分开：

1. `.111` 没有 dispatch 到玩家经理；
2. `.111` 以合法 ticket 进入 success 分支，但
   `zg361_b1_open_calibration_effect` 的入口 guard 未通过。

第二种解释与 fresh cycle 的写入不变量不符：本周期 D0 会把
`zg361_b1_calibration_finalized` 初始化为 `0`，而该变量只有 calibration finish 才会置为
`1`。同时，若 calibration 真正进入，代码会先把 cycle state 写成 `7`；若 quick-close
失败则会恢复 `6` 并留下明确日志。因此，当前证据最支持第一种解释，但本记录不把推断
提升成已直接观测的事件队列事实。

这不是新的加载性能 RED。相同 PID 已完成 exact-build loader gate 的 303/303 database
nodes，fatal count 为 0，并在地图内推进超过两个完整 B1 机会窗。故障属于运行期状态机
liveness，不以继续延长观察窗或再次拆分既有 B1 effect 文件处理。

R179 原 session 仍是 production-live RED；下文的 D+340 watchdog 只能标记为
`static-fixed/live-pending`，不得据静态结果声称 live 已修复。

## 冻结 artifact

### R179 continuation

- 汇总报告：`Z:\p2r179promo_resume\report.json`
  - SHA-256：`747C9EE049DA27B294A1597AEDB65502358B37F6DE093C207459BBD80535A4A6`
  - bytes：`47135`
- 产品入口证据：
  `Z:\p2r179promo_resume\03_promotion_source_production_entry.json`
  - SHA-256：`95E52FE4D31D92CF47A9A12459ECAE7C1A4EBABADC12074B46F632BFF633B4ED`
  - bytes：`39927`
- reconnect 后 runtime diagnostics：
  `Z:\p2r179promo_resume\02_retained_runtime_diagnostics.json`
  - SHA-256：`334A1600875183D62D6F05CB3C5487E221B8AF979D03A5F14159DF64D26A6C61`
  - `blocking_diagnostic_count = 0`
  - 扫描基线：`error.log=3564980`、`debug.log=689497`
  - reconnect observed offset：`error.log=3583173`、`debug.log=922434`
- retained state：`Z:\p2r174promo_a_native_state`
- live profile：`Z:\p2r174promo_a_native_state\profile`
- live logs：
  - `Z:\p2r174promo_a_native_state\profile\logs\debug.log`
  - `Z:\p2r174promo_a_native_state\profile\logs\game.log`
  - `Z:\p2r174promo_a_native_state\profile\logs\error.log`
- CK3 PID：`68028`；R179 `source_pid=live_pid=68028`、`restart_count=0`，报告保留
  session 供后续只读或受控接续。

### 实际产品投影

- staging：`Z:\p2p164\p`
- projection receipt：`Z:\p2p164\phase2-product-projection.json`
  - projection：`phase2-full-release-r164-7b01124`
  - files：`1031`
  - receipt SHA-256：
    `9C9C84F828D5CCC795D4F43454F4BC3E5B6061CD97BFF8DFDB829386DFB367D8`
  - source tree SHA-256：
    `E9F093A2DBBA3120F7A06FF65E08B5AA9C0A438D5FD8A582A22EC62DBF63A99D`
  - formal overlay tree SHA-256：
    `2A1501DF2A169FD97761D7149F63D729A4DB9E57F86BEE685D902BAD0FF17FCA`
- release manifest：`Z:\p2p164\p.manifest.json`
  - SHA-256：`5BAF6520FBE5601CCE098FEC0F3148AF795F8D0E977506D5699674EC1D2D208C`

### 冷启 loader 证据

R179 复用的 PID 来自 `Z:\p2r174promo_a\report.json`：

- `loader_gate_evidence.result = GREEN`；
- `state = loader_stage_ready`；
- `stage = load_save`；
- `database_init_seen = true`；
- `database_node_count = 303`；
- `fatal_error_count = 0`；
- tracked PID 同为 `68028`。

## 时间线硬证据

R179 报告把时间预算绑定在 immutable product origin，而不是每次 reconnect 重置：

- origin：`date_raw=53147016`；
- 本 continuation 起点：`53163168`；
- absolute end：`53173416`；
- 总预算：`2 * (400 authored B1 days + 150 post-publication days) = 1100 days`；
- 最后一个成功暂停观测：`date_raw=53173392`，仍为
  `review_now_eligible=false / B1=true / Central=false / PP=false`；
- 随后正确报出 observation-bound RED，没有把等待冒充交付进展。

live `debug.log` 的关键行如下：

| 行 | 时间 | 已证明的业务边界 |
|---:|---|---|
| 4209 | 06:02:54 | `ZG361B1: performance season opened` |
| 7812 | 06:19:26 | `ZG361: annual review tick` |
| 7835 | 06:19:26 | `ZG361B1: facts frozen and shadow response opened` |
| 7909 | 06:19:27 | `ZG361: annual B1 request deferred behind an active serial consumer` |
| 8056 | 06:21:55 | `ZG361B1: local quota reranked by bounded post-shadow calibration score` |
| 8059 | 06:21:55 | `ZG361B1: exact quota bank closed with at most one unique same-function 3+4 pool` |
| 8068 | 06:21:55 | `ZG361B1: stale common-superior bank ticket ignored` |
| 11712 | 06:22:36 | `ZG361: duplicate deferred annual B1 request coalesced` |

`8068` 不是根因。正常的 early close 已把 bank state 从 `1` 写成 `2`，原先在 D335
排队的 `.110` deadline 随后到达时必须按 immutable ticket 契约成为 stale no-op。

从 line 8059 到日志末尾，下列任何一个本应区分后续分支的 marker 都没有出现：

- `ZG361B1: stale manager-calibration ticket ignored`；
- `ZG361B1: incomplete manager-calibration ticket ignored`；
- `ZG361B1: B quick-close assignment/quota mismatch; calibration withheld`；
- `ZG361B1_DIAG: human pending/reopen route evaluated`；
- `ZG361B1_DIAG: human closure gate evaluated`；
- `ZG361B1_DIAG: human calibration finish evaluated`。

`error.log` 没有对应的项目运行时错误；R179 diagnostics 对 reconnect 增量扫描 161 项，
blocking 项为 0。三个记录到的 nonblocking warning 都是原版 `dynastic_cycle` situation
参与者移除警告，与 B1 callback 无调用关系。

## 源码关联

以下位置均指实际产品 `Z:\p2p164\p`：

1. `common/scripted_effects/zg361_b1_runtime_002_cycle_self_review_effects.txt:98`
   初始化 `zg361_b1_calibration_finalized=0`；`:183-191` 注册 common-superior bank，
   并排队 D180 主链。
2. `events/zg361_b1_runtime_events.txt:262-340` 的 `.103` 在 D300 后再等 D30，
   将 manager state 写成 `6` 并提交 quota book。
3. `common/scripted_effects/zg361_b1_runtime_004_quota_bank_debt_effects.txt:1144-1189`
   登记 ready manager；最后一个 expected manager 到齐时排队 early `.110`。
4. `common/scripted_effects/zg361_b1_runtime_005_huddle_agenda_effects.txt:398-725`
   完成 exact bank close；`:707-721` 对 ready manager 冻结 state-6 ticket，并排队
   `zg361b1.111 days=1`。
5. `events/zg361_b1_runtime_events.txt:421-445` 的 `.111` 校验
   owner/cycle/case/state，成功后调用 `zg361_b1_open_calibration_effect`，失败则各有
   stale/incomplete marker。
6. `common/scripted_effects/zg361_b1_runtime_009_calibration_controls_publish_effects.txt:580-644`
   要求 `cycle_state=6` 且 `calibration_finalized=0`，成功入口首先把 state 写成 `7`；
   quota/assignment quick-close 则恢复 state `6` 并写 marker。
7. `common/scripted_triggers/zg361_triggers.txt:22-39` 明确 review-now 在 active B1 或任一
   serial dependent active 时不可用；它不是 state-6 卡死的旁路。
8. `common/scripted_effects/zg361_jingcha_mandate_effects.txt:36-66` 对 active serial
   consumer 只记录并合并 pending annual request。line 7909/11712 正好证明该分支按设计
   工作，但它不会重新触发 calibration。

## R96 对照

R96 的 frozen product 位于 `Z:\p2r96\p`：

- projection receipt：`Z:\p2r96\phase2-product-projection.json`；
- projection：`phase2-full-release-r96-7ac52c0`；
- files：`937`；
- source tree SHA-256：
  `8F2C862913A4FEEC717D8BB4A48065B513B532655D58E3A238AEBF8F6850FE44`；
- release manifest SHA-256：
  `8E9C29A29236FE1BC0BE0C1E1AC83C8B75D1C161DFBBA101F5C25516DFA3EAD4`。

`promotion-source-checkpoint-choreography-forensics-2026-09-04.md:1228-1249`
记录 R96 fresh schema-v2 周期从
`B1=true / Central=false / PP=false` 实际变为
`B1=false / Central=true / PP=false`，随后进入 Career/HC。

R96 与 R179 产品中的 bank-close 尾部都采用“遍历 ready managers，写 state 6，排队
D+1 `.111`”的相同模式；`.111` 的 owner/cycle/case/state guard 与
`open_calibration` 调用也相同。附近可见差异只是 quota pool iterator 的
`max=7` 改为 `max=list_size:...`，不涉及 callback。这说明 `.111` 链不是静态必败，
同时也证明仅有这一条 common-superior 派生的回调不足以覆盖本次真实 retained/live
时序。

## 已实现修复：manager-owned D+340 state-6 watchdog

### 为什么是 D+340

ready managers 全部提前提交时，early close 可以早于 D335，并随即排队 D+1 `.111`；
若没有提前闭合，bank deadline 路径在 D335 close，最晚于 D336 执行 `.111`。D+340
因此严格晚于两条正常 close 路径，既不会抢跑 quota bank，也能在 400 日 authored B1
窗内给 calibration、pending 与 publication 留出剩余时间。

实现从 D0 的 manager-owned `zg361_b1_open_cycle_effect` 排队 watchdog，没有再次从
common-superior `ready_managers` list 派生，因而不复用本次发生故障的同一依赖。

### 严格 no-op 合同

实现使用此前空闲的 hidden character event `zg361b1.112`，以及独立字段
`zg361_b1_calibration_watchdog_owner/cycle/case`，没有复用会被 `.100`–`.111` 连续
改写的通用 `zg361_b1_ticket_*`。

`.112` 只有同时满足以下条件时才能调用唯一 canonical
`zg361_b1_open_calibration_effect`：

- event root 仍 alive，且 `is_ai = no`；
- `this = scope:zg361_b1_calibration_watchdog_owner`；
- `has_character_flag = zg361_b1_cycle_active`；
- 当前 `zg361_b1_manager_cycle_serial = scope:zg361_b1_calibration_watchdog_cycle`；
- 当前 `zg361_b1_manager_case_serial = scope:zg361_b1_calibration_watchdog_case`；
- `zg361_b1_cycle_state = 6`；
- `zg361_b1_calibration_finalized = 0`。

以下情况必须严格 no-op，且不得恢复旧 serial、不得重开 bank、不得重排 quota、不得
重写 subject list、不得发奖励：

- 正常 `.111` 已把 state 推进到 `7` 或更后；
- 本周期已经发布或关闭，active flag 已移除；
- 新一周期已经轮换 cycle/case；
- ticket owner 已失效或死亡；
- calibration 已 finalized；
- 任一必要变量缺失。

成功 guard 只调用既有 canonical effect，并写一条专用 debug marker
`ZG361B1: manager calibration seam recovered by D340 watchdog`；event 自身一次性消费，
不进行轮询。该边界使 watchdog 只修复已实证的 state-6 liveness 缺口，不产生第二套
calibration 实现。

### 生成器与测试入口

- D0 ticket/schedule：
  `mod_zhongguo_style/tools/gen_361_b1_runtime.py:2150-2153`，现有 D180 ticket 前；
- `.112` event：同一生成器 `:9676-9704`；
- `mod_zhongguo_style/tools/test_zg361_b1_runtime.py:327-344`：manager identity
  migration event 集加入 `.112`；
- 同测试 `:515-541`：独立 immutable ticket、D340 schedule 和 stale/no-op marker；
- 同测试 `:2883-2910`：断言 watchdog 不从 ready-manager bank-close loop 派生，且只调用
  canonical open-calibration effect。

修复已经改变生成的 mod bytes。当前 PID `68028` 不会热加载新定义，而当前旧存档也没有
D0 时排队的 `.112`，因此最小产品验证是重新生成投影并从 canonical seed 冷启一次
CK3。若目标改为救活当前旧 state-6 save，必须另加 load/annual recovery seam；那不是
本次 fresh acceptance 的最小修复。

### 已完成静态闭合

以下结果已由实现工作包完成，本记录只将结果与根因证据对齐，不把它们升级为 live：

- `py mod_zhongguo_style/tools/gen_361_b1_runtime.py --check`：GREEN，生成结果与生成器一致；
- `py mod_zhongguo_style/tools/test_zg361_b1_runtime.py`：`75/75` GREEN；
- `py -O mod_zhongguo_style/tools/test_zg361_b1_runtime.py`：`75/75` GREEN；
- `py tools/validate_static.py`：GREEN；
- 修改后的生成器、生成事件、D0 schedule 和聚焦测试通过 `git diff --check`。

这些检查证明 source/generator/generated/test 契约闭合；只有下一次 fresh product CK3
运行能够证明 `.112` 在真实 state-6 stall 上恢复 calibration，或在正常 `.111` 路径上
保持严格 no-op。

## effect 分片边界

R179 实际产品的 13 个 B1 purpose effect shards 顶层 effect 数依次为：

`8, 10, 9, 8, 7, 6, 9, 4, 6, 5, 3, 4, 1`

全部处于目标 `1-10`，没有超过 `20` 的例外。已实现的 D0 排队语句进入已有
`zg361_b1_open_cycle_effect`，`.112` 是 event，不新增顶层 scripted effect，因此按上述
实现，effect shard 计数保持不变。若后续确需抽出独立 recovery effect，应放入当前
只有 1 个 effect 的 `zg361_b1_runtime_013_cycle_migration_recovery_effects.txt`，不能让
已经有 10 个 effect 的 `_002_cycle_self_review_effects.txt` 超出目标上限。

## 下一轮验收判据

1. 已完成的 generator `--check`、B1 `75/75` normal、`75/75 -O` 与
   `validate_static` GREEN 保持不回归；
2. fresh product loader 303/303、fatal 0；
3. 正常 `.111` 成功时，D340 `.112` 为 no-op，不能产生第二次 calibration/publication；
4. 若 `.111` 再次没有产生结果，D340 必须留下专用 recovery marker，并在同一 manager
   cycle/case 上进入 state 7；
5. 最终必须实机观察到 `B1=false / Central=true`，继续到真实 `zg361pp.146/.147`；
6. 不得以 ACK、fixture flag、静态 schema 或延长 observation bound 代替上述业务状态。
