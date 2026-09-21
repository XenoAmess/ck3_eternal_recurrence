# G2 ordinary / GEN-034-D R0027 vacation handoff

交接时间：2026-09-21（Asia/Shanghai）

## 用户现在能拿到什么

**当前已有可取得、可启动、可受控停止并可新进程冷恢复的 R888 GO 预览包。**

- ZIP：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r888-d559faa6-stage-20260921\g2-preview-ordinary-d559faa6-r888.zip`
- ZIP SHA-256：`F7FAC0F56AB438548F8385C2901BFABE89BCBEEA840E6B46A3C7D1779118E9F6`
- live qualification：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r888-d559faa6-qualification\g2-preview-ordinary-d559faa6-r888-live-qualification.json`
- qualification SHA-256：`0A74F8226407CC087A73ECB84B29FC80A3E3B4B3E821CBEA2EEE431B343E2757`
- 经实机验证的启动、状态、受控停止、checkpoint、冷恢复命令与支持边界：
  [`../ck3-native-ai/g2-preview-release.md`](../ck3-native-ai/g2-preview-release.md)

这个交付是冻结的标准封建 ordinary bounded continuation，不是任意用户存档、1066→1453 整局或 G2 complete。
权威状态仍为 **G2 1/8**（仅 M1）、**Council 1/4**、**GEN-034 3/4**。R0025–R0027 没有新增
完整里程碑，不能改变这些计数。

## Git、运行时与当前现场

- 本次交接文档提交前的远端/本地基线：`master@d044e7523dc87ffa4613da2e9a72b2328abf31f8`；本文自己的最终提交以 Git 历史为准。
- `55429bfbc1c6409f3747ce9a8e257eff19642a1a`：continuation runner 将 cold-start readiness 从旧 live-manifest
  attach budget 解耦，新增 `--readiness-timeout`，默认 `720s`。
- `d044e7523dc87ffa4613da2e9a72b2328abf31f8`：重新冻结 481 文件 runtime closure；manifest SHA-256
  `EF05222DA1C124F27A9EDEAFE3C4A3A5A1012331D3125D529CBBAF78F4E8A492`，tree SHA-256
  `8DDCFEA7D07CA61C03181791CC27AF6B3E3C98FB984A1436F81B425A38132154`。
- continuation live-adapter manifest SHA-256：`A4AF2689F6ADF688CF6C431F5AC0396F9AD43E247AB5643518795545E4B4B943`。
- exact no-launch preflight：
  `Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-continuation-preflight-d044e752-20260921\adapter-preflight.json`，
  SHA-256 `C8767DACA714C355AB63A5E2198BF155E87AB26AAD5D9CED7473178CDA8A0E7E`，状态 READY。
- 正确冻结解释器只能用 `Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe`，SHA-256
  `D70FCED7F461F38F9F224D8673FB74E96E4FACB4283FF4E8697543B457FEA8A0`；不要改用系统 `py` 或 `py -3.13`。
- 当前 CK3 / injector 进程为 0；Git 只剩当前 `master` worktree，没有活动临时分支或运行 worktree。

聚焦 continuation/runtime-manifest/live-adapter/native-auto-run 测试已在 normal 与 `-O` 各通过 `132/132`；runtime
manifest verify GREEN。没有为该局部修复重跑全量 CI。

## R0025–R0027 continuation 结果

| canonical / legacy | 结果 | 可复用结论与证据 |
| --- | --- | --- |
| R0025 / R894 | `completed-red` | 旧 runner 把正式冷启动 readiness 错绑到 `bridge_attach_seconds=60`；61.572 秒时 bridge、build 与 adapter 已就绪，但 map 尚未 ready、date 为 0，`attempted_turns=0`。外层 report SHA `AF60DDE3E7CB11062592DA3A83B1D7E101965664BA89541B7477E1146A87863F`，native report SHA `1D936E0ECD0D4C25C74D8AD1A48CE6DE0AB5EF50F4148B5C2AA18ECAEA8000ED`。进程回收 GREEN；该实证直接驱动 720 秒 readiness 修复。 |
| R0026 / R895 | `completed-red`、未创建 CK3 | 通过正式 state preparation 前因误用系统 `py -3.13`，缺少冻结环境要求的 `nvidia-cublas`；report SHA `88280B717F9A84FB28725CE2A2AE0B22F73F12390DFDC0A7E2CF254C70C27A50`。这是操作器解释器漂移，不是依赖合同错误；不得放宽依赖门。 |
| R0027 / R896 | `completed-red`、真实 first turn | 正确冻结解释器下，formal prepare/rebind/checkpoint/runtime closure 全部 GREEN。新 CK3 PID `27616` 在 95.026 秒达到 map-ready，date `53173176`、actor `29829`、WarID `16777285`、checkpoint restore 与 mailbox 均就绪，证明 readiness 修复生效。随后正式首 turn 的公共 campaign-root query 被 native 接受，但 Python 合同拒绝畸形 held-title partition：`held_title_partition[1].capital_province_id must be present only for a county`。`attempted_turns=1`、successful/action/date advance 均为 0，未生成 terminal plan 或 action-runner input；cleanup GREEN。外层 report SHA `FEFC9A11E2F750347F9A3CDBE159F1D6862FE4D13824B8788AC77E4554B98CCA`，native report SHA `74CA99461FB036921588F8552D237FAD1959ADF5AD7C190D1EAE72F5B3A36666`。 |

R0027 的原始 paused payload 保存在
`Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-continuation-d044e752-r0027-20260921\candidate-continuation-attempt-01-formal-state\native-session\driver-state.json`。
关键行是：duchy `2141 / tier_raw=3 / capital=null` 合法；county `2142 / tier_raw=2 / capital=null` 与 county
`2173 / tier_raw=2 / capital=null` 违反合同，同时 native 仍错误发布 `held_title_partition_ready=true`。

[`campaign-root-context.md`](../ck3-native-ai/campaign-root-context.md) 与
`ck3_autonomous_player/native_bridge/research/campaign_root_context_v1_abi.json` 的既有合同要求 county
必须有非空 resolver 结果；解析失败时完整 partition 不得宣称 ready。Python normalizer 的拒绝是正确 RED，**不得把 null
改成合法、删除字段或放宽 validator**。当前根因已缩小到 exact-build native campaign-root producer 的 county-title
capital resolver/ready advertisement。

## 不可变 R0024 source 与恢复边界

继续复用下列自然创建来源，不重新制造 source，也不在结果未知时提交终局动作：

- root：`Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-candidate-b9e3357d-20260921`
- 六源 capture：`candidate-live-attempt-01\capture.json`，SHA-256
  `FF76C8E14DA90959303DEF32AB601C6DA44C4D737AA1484E342CD70DC3B7EB04`
- checkpoint：`candidate-state\profile\save games\xar_checkpoint.ck3`，history `1`、date `53173176`，SHA-256
  `2661E9F0717521BBE7F8B7D8554331CA56F1D850D7FE9186704D3B7125A8F8D9`
- driver：`candidate-state\native-session\driver-state.json`，SHA-256
  `BC0B9BD103C8265F67B1F6ECE77DE79CE85F5FCA23F310F4D034895C7B8B7ADD`
- identity：actor `29829`、WarID `16777285`。

R0025、R0026、R0027 均在报告中再次确认这三份 source 输入哈希未变。各轮 formal state 是独立副本；不要把失败
attempt 目录当作下一轮可写 state。

## 下一位执行者的最短关键链

1. 冻结 R0027 使用的 exact bridge source/binary 与 CK3 `1.19.0.6`（EXE SHA-256
   `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`）；直接从 R0027 raw query 和当前
   ABI 台账定位 county title `2142/2173` 的 native capital resolver，不扩展无关观测面。
2. 优先让 producer 发布真实 county capital ID；若 exact frame 确实无法解析，则必须把 held-title partition 标成 unavailable，
   不能同时返回 null county capital 与 `held_title_partition_ready=true`。因为该字段会阻塞正式决策，最终仍需补成真实可用观测，
   并用 exact paused snapshot 验证。
3. native 改动后跑受影响的 MSVC Release 构建、campaign-root 聚焦测试以及 Python normal/`-O` 消费测试；保留已有
   validator，不用测试绿灯替代实机 paused snapshot。
4. commit 后只用 rebase 整理并普通 push `master`；重新冻结 runtime/manifest，创建新的干净 runtime worktree，并重做
   exact no-launch preflight。
5. 在全部受管环境再次确认 process-zero 后分配 **R0028 或更高的实际新编号**（legacy R897 或更高），使用正确绝对
   venv 解释器，从不可变 R0024 source 生成新的 attempt/formal-state 目录。不要盲目重跑 R0027 现有目录。
6. 只有 production `native_auto_run` 真正返回 matching terminal intercept 并生成绑定现场的
   `action-runner-input.json` 后，才能另分配新轮次运行唯一 emitted command。随后仍须完成同帧三路比较、唯一 typed
   终局动作、独立物质后置、checkpoint、新进程 cold restore、下一 turn 消费和零重放；ACK 不作生效证明。

## 工作区与磁盘清理

- `C:\workspace` 原有 44 个 Git 目录；已逐项核对集成状态。33 个 clean tip 已在 master，6 个非祖先临时分支经
  `git cherry` 确认为 patch-equivalent；已删除对应远端缺席的本地分支、7 个 worktree 与失效 tracking refs。
- 已清理的脏垃圾包括两个只有畸形 `C/.../CMake*` 产物的 clone、一个 HEAD 已进 master 但工作树呈 7405 个 staged
  deletions 的损坏 clone，以及旧 build/review 输出。没有把这些垃圾提交。
- R883 未提交的 539 行 same-current route-cancel 实验已丢弃：R886 实机已证明动作不可达，master 又已有
  `01a2295b` 撤销提交；它不是待交付改动。
- 已删除冗余 `C:\workspace\Crusader Kings III` junction，目标 `Z:` 游戏目录未动；已删除约 241 MiB 旧 workspace
  build artifact。`%TEMP%` 仅删除超过两天的文件，共 40,505 个、13,331,638,693 bytes（约 12.42 GiB）；52 个锁定文件跳过。
- 当前 `C:\workspace` 只剩 `ACM_JAVA`、`elona_cheat` 与本仓库；前两者是无关用户目录，未删除。运行 artifact、日志、
  checkpoint 保留在独立的 `D:` / `Z:` 证据目录，不能当垃圾清理。

## 兼容与广告边界

readiness timeout 修复只改变内部 runner 参数，没有公共 MCP schema、能力广告或 open_kaishek 接口变化。R0027 暴露的是
既有 native campaign-root producer 的 exact-build 实现错误；下一次 native producer 修复若改变字段可用性、manifest 或二进制，
须同步更新 MCP/ABI 资产和简短兼容说明，但不能通过适配层掩盖错误值。当前不需要 open_kaishek 改动。

R888 预览包保持可交付；Council guest/pending/replacement 三门、GEN-034-D、指定自然事件、同一 ordinary campaign
自然继承、两年治理、家庭外交、首条整局、第二种子及 G2 广矩阵继续未广告。未知强制状态仍 fail-closed。

## 读取顺序

1. 本文与 [R888 用户交付页](../ck3-native-ai/g2-preview-release.md)；
2. [G2 权威合同](../autonomous-agent-progress/g2-requirements-v1.json)；
3. [GEN-034-D candidate builder/continuation 记录](../ck3-native-ai/gen034-d-candidate-builder-2026-09-21.md)；
4. [当日日报](../autonomous-agent-progress/daily/2026-09-21.md) 与 [本周周报](../autonomous-agent-progress/weekly/2026-W39.md)；
5. R0027 outer/native reports、raw driver state、launch contract，再回看不可变 R0024 capture/checkpoint/driver。
