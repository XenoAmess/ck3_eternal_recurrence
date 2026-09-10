# T0 天朝二期进度延期复盘

时间：2026-09-10 21:58（Asia/Shanghai）

结论：这是执行与验收管理失败，不是“工作量不够”。从 `5497920`（09-09 18:29）到
`1b2c391`（09-10 21:42）约 27 小时产生了 125 个 first-parent、零 merge 提交，但正式
P1 机器门仍为 `1/9`，净增为 `0`。这些提交有各自价值，却没有被我有效转化成当前最高
优先级的可签收结果。此前继续用历史 `T0 50% / stage 8/11` 描述当前进度，以及用提交、
测试和资产数量说明“进展很大”，都是错误的汇报。

## 延期事实

| 原节点 | 承诺 | 实际结果 | 截至 09-10 21:51 的偏离 |
|---|---|---|---:|
| 09-07 日计划 | 当天完成完整迁移树验收 | 09-08 00:00 仅 `stage 8/11` | 约 69 小时 51 分 |
| 09-08 日计划 | 当天恢复并完成迁移树推进 | 09-09 00:00 仍 `stage 8/11` | 约 45 小时 51 分 |
| 09-09 日计划 | 完成第 4 source 与 stage 9–11 | 09-10 00:00 为 source `3/4`、`.356` `2/3`、stage `8/11` | 约 21 小时 51 分 |
| 09-07 15:50 重估 | 09-08 至 09-09 完成 AF5、stage 9–11、`7+4+restore`；P1 GREEN 后最早 09-09 至 09-10 进入视频 | 当前 P1 未签收，P2 仍锁定 | 整个日期窗口已落空 |

当前九项门的诚实状态是：最终候选 L0 已接纳 `1/9`；R390 的 B1 与受管清理已有
immutable GREEN 证据，但尚未进入最终 evidence manifest，且中间清理不能预先冒充最终候选的
managed-cleanup 门。AF5、stage 9、stage 10、stage 11 terminal、cold restore、完整 gameplay-window
error scan 和最终清理仍未签收。因此当前 P1 机器门完成度是 **11.1%（1/9）**，不是 50%。

## 为什么会这么慢

### 1. 我先施工，后固定验收分母

九项机器门直到 09-10 12:16 的 `d7a7c40` 才正式固定。此前我持续围绕 source `4/4`、
第三次 `.356`、全树长链和历史 stage 口径调度。R304–R326 用 23 个轮次取得的两个 source
checkpoint、R372 满 6 小时追逐的第三次 `.356`，后来都被现行口径明确降为 non-blocking。
范围裁剪是用户要求，我没有及时把执行拓扑和进度分母一起切换。

### 2. 我把独立的门错误绑在一条自然长跑谱系上

B1、AF5、stage 9–11、cold restore 本可分别使用 hash-bound 真实 checkpoint。相反，我长期试图
让一条随机长时间线承载多个门。其结果是 6 小时 supervisor timeout、随机原版事件不断串行插入，
以及 `tgp_dynastic_cycle.0081` 的不可逆 chaos 直接使谱系不再适合作为后续 terminal 证据。直到
R390 后才确定 split acceptance，改线太晚。

### 3. 我把可复用资产义务放进了 CK3 串行关键路径

保留真实 RED、查 exact-build、做最小安全合同并热恢复是正确要求；把已有和新增事件知识沉淀为
通用 MCP 资产也是用户明确要求。错误在于我经常等完整 registry、analysis、observation、文档、
大套件和 CI 全部串行完成后才恢复健康 PID。存量迁移和资产丰富化本应由独立工作流并行，不能
阻塞当前事件的“最小合同 + 聚焦双模式 + 同 PID 恢复”。合同数、caller 数不是 T0 进度。

### 4. 启动前测试没有覆盖最高价值状态边界

今天的三个产品 RED——persistent roster 大小读取、final callback prune 后未重新封账、Stage 11
首次进入读取未初始化 optional 变量——都属于 first-entry / last-mutation / invariant 边界。这些
不需要审完 626 个 definition；少量定点 fixture 就应在启动前发现。Stage 11 修复虽然累计跑了
数千项测试，仍只是 static-ready，说明测试数量替代不了关键状态覆盖。

### 5. 我在已存在可用操作者时仍错误等待 MCP 换人

11:35 已知 CK3 为 0；14:37 仍在等待另一个 `127.0.0.1:8766` operator endpoint；15:19 才确认
当前会话本身就是 `xenoa / WinSta0\\Default`，可以自行启动通用 operator MCP。CK3 关键槽至少
空转约 3 小时 44 分。可迁移 MCP 是长期要求，不应成为当前可用操作者启动 CK3 的前置条件。

### 6. wrapper 缺陷消耗了过多独占轮次

R377–R390 间先后出现 callback 未注册、双归一化、错误的 10190-day 起点、snapshot publication
race、roster 与 survivor 收口缺陷。R251–R280 更曾有 29 次 CK3 启动全部消耗在 loader/VFS/图形
诊断，产品门增量为 0。这些故障有技术价值，但我没有及时改用可用 operator，也没有把完整
no-launch 端到端 fixture 作为下一次启动的必要输入。

### 7. 并发很宽，但关键路径没有被保护

事件迁移、G2、CoA、operator MCP、其他产品宣传和报告工作可以并行；我却让它们共享主协调、
rebase、生成目录和验收注意力。Stage 11 还发生过两个会写同一 generated tree 的测试并发，产生
一次假失败和整套串行重跑。用户要求宽并行，不等于允许 T0 控制流被支线切碎。

### 8. ETA 与汇报方法不合格

我报的是“没有新 RED 时的最快路径”，没有给 checkpoint 适用性、启动次数、迁移失败和原版事件
插入留出显式风险，也没有在 09-08 第一次 miss 时立即宣布偏离。此后固定复述 50%，掩盖了
burn-down 没有变化。责任在我的估时和汇报，不在验收标准“太严”。真实产品 RED 必须修；可避免的
是让它们到长跑后才暴露，以及让无关工作进入关键路径。

## 即刻纠偏

1. P1 只报 `x/9` 与本轮净变化；未被 evidence manifest 接纳就不加分。提交数、测试数、合同数只作吞吐旁证。
2. 一个 CK3 轮次预先只声明一个验收目标、输入 SHA、最长时间和停止条件；没有目标结果，不派生新的审计专题。
3. 使用独立短 checkpoint：Stage 11 首入归零、AF5、不同谱系 stage 9–11、terminal cold restore 分开取证。
4. CK3 运行时并行准备下一包的 profile、哈希和 manifest 草稿；唯一 CK3 owner 不兼任支线集成。
5. 新原版事件只执行 SOP 的最小闭环。存量迁移、额外 MCP 索引和文档丰富化并行，不等待它们才热恢复。
6. 启动前必须一次通过 callback 注册、normalizer 端到端、wrapper 起始 substage、product/bridge/checkpoint 哈希四项检查。
7. 同一 generated/build/runtime 目录只能有一个 writer；normal 与 `-O` 若会写同一树就串行。
8. 完整 L0 只对冻结候选执行；代码或产品树 SHA 改变才使其失效。已有同 SHA 结果不重复跑。
9. 当前账户有能力且 CK3=0时立即经 operator MCP 启动，不再等待假设中的另一位操作者。
10. ETA 以后给门级区间和失效条件；第一个条件失效时立即更新，不等到节点过去。

## 直至 P1 `9/9` 的停止清单

- 不做 361 严格场景、626 definition、source `4/4`、第三次 `.356`、三周期或旧 `7+4` 矩阵；
- 不碰 T0-P2 宣传工具、素材和最终视频；
- 不展开非当前 blocker 的存量事件迁移、新 MCP 架构、CoA、D2 或 G2 live；
- open_kaishek 仅在公共 API/schema/ABI 真变化时同步；
- 不做理论安全审计、重复全仓扫描、同输入无新证据的多次重启。

## 恢复节点

以下是**无新产品 RED 时**的门级执行窗口，不是用日历强行把 RED 写成 GREEN。任一窗口超时都必须
冻结精确失败、切到既定替代 checkpoint，并立即报告新的 `x/9`，不能继续报主观百分比。

| 上海时间 | 目标 | 时间上限 / 退出条件 |
|---|---|---|
| 21:58–22:30 | 复盘提交；修正 Stage 11 no-launch game-root 预检 | CK3 保持 0；profile、checkpoint、projection、DLL、原版 rule 文件哈希全部 GREEN |
| 22:30–23:25 | 串行 frontend warm-up + Stage 11 首入复验 | 到 `zg361we.242` 停车；旧 5 变量/15 诊断为 0；不冒充 terminal |
| 23:25–00:15 | AF5 独立 checkpoint | `.147` → `zg361comp.1` authored 42/native 41 → provider terminal；否则保留精确 RED |
| 00:15–01:00 | legacy celestial 存档的 1.19.0.6 无 mod 准入与 MCP 重存 | 15 分钟准入失败即切备选，不在旧存档上展开逆向 |
| 01:00–02:45 | 当前候选下的 stage 9、10、11 terminal | 三个独立 provider receipt；每个 stage 25 分钟无前进即停车取证 |
| 02:45–03:30 | terminal cold restore、全窗 error scan、最终 cleanup、L0 与 manifest | 四域前后相同、blocking diagnostics 为空、cleanup GREEN、最终 `9/9` |

最佳无新产品 RED 目标修订为 03:30，恢复缓冲截止为 04:15。若出现真实产品 RED，完成时间由该 RED 的
最小闭环决定；04:15 必须给出精确未闭合门、artifact 和新节点，禁止继续沿用失效 ETA。

当前可立即执行的输入：Stage 11 runtime-only MCP 包已在
`_runtime/r391-stage11-smoke-mcp/` 完成 normal/`-O` 各 `6/6` 与 operator preflight，manifest
SHA-256 为 `DAD054B7281D6267535784EDF723934F4C5DD76DE2ADF79FB4B7A8428A429505`；当前 CK3 inventory
为空。该包会诚实记录 frontend warm-up 与 loaded-save 为两个递增轮次，始终只保留一个 PID。

22:10 的首次 MCP control 在 CK3 启动前保留了 harness RED：wrapper 从隔离 worktree 错推原版
`00_game_rules.txt`，而真实文件位于仓库根的游戏目录。artifact SHA-256 为
`3FFAA8AB1A325FE252A31BDC31A691967007699A63DBC719024FED5A9AA6BF11`，包含错误文本的 operator
stdout SHA-256 为 `430722ADDD59B2891BBB3EE95B4FC3FC3F820C2B1E6195D0E00476EAA83C2FDE`；
`launch_count=0`、`product_result=NOT_EVALUATED`、CK3=0，故没有创建新轮次。该失败暴露了 preflight
遗漏，修复仅允许把 exact game root/rule 文件作为 profile 的 hash-bound 输入并补 no-launch 测试，不能扩成
新 MCP 架构。Stage 11 窗口因此顺延 15 分钟，P2 的 09-11 18:00目标暂不变。

## 从 P1 到最终宣传片的补救交付计划

9 月 9 日交付目标已经失败。新的主目标不是“本周内”，而是 **9 月 11 日 18:00 前完成机器可控的
P1、P2 制作、导出与发布链**。这个目标建立在“至多一个新的产品 RED、至多一次视频重制、所需发布会话
和具名人工签核可用”的条件上；不是无条件保证。若没有新产品 RED，P1 目标修订为 09-11 03:30，缓冲到
04:15；若出现一个可热恢复的最小合同 RED，P1 恢复目标为 09-11 10:00。

P1 GREEN 以前继续严格执行视频硬锁。解锁后按固定顺序推进，不能把历史工具版本检查冒充本次前置：

| 上海时间（目标） | P2 工作包 | 交付判据 |
|---|---|---|
| P1 GREEN 后 0–30 分钟 | 检查宣传工具、`fetch`、rebase/fast-forward 到远端 `main`、验证 clean/HEAD 一致 | fresh tool receipt 与精确 HEAD/SHA；失败不制作媒体 |
| 随后 20–50 分钟 | 一次受管 CK3 capture + intake | `8/8` clean spans、同一 intake 的 report/timeline/evidence/loaded-seed 哈希闭合 |
| 随后 30–60 分钟 | 两版 source review/claims binding | 八段原始素材与两个 cut 的 source receipt 完整；不得用模板冒充签核 |
| 随后 45–90 分钟（两版并行） | TTS、字幕、人物版与制度群像版候选构建 | 两条候选 MP4、ffprobe、storyboard、自动媒体审计 GREEN |
| 随后 60–120 分钟 | 两版独立完整审阅、必要的一次重制、最终 export | 对最终精确字节的 review/sign-off、export manifest、SHA-256 完整 |
| 随后 20–40 分钟 | 授权发布与远端回读 | 两条发布回执、远端 locator、最终 hash 对应一致 |

机器路径无 RED 的最早可交付窗是 09-11 上午；为人工审阅、一次重制和发布回读预留后，负责人目标为
**09-11 18:00**。若出现第二个产品 RED、宣传工具上游破坏性变化、发布凭据/会话不可用或具名人工签核
不可用，必须在 20 分钟内报告事实、artifact 和新的门级时间，不得静默消耗到周末。一个产品 RED加一次
视频重制的保守恢复上界是 **09-12 12:00**；超过它必须证明具体外部阻点或未闭合产品门，不能再用
“还在测试”概括。

为了保护这个交付目标，主控制流在 P1/P2 完成前只做 T0。T1 仅允许独立 worktree、无需 CK3、无需共享
generated/build/runtime 写面的既有非冲突工作继续；不启动 G2 live，不引入新的公共接口。T2 仅在 T0/T1
真的改变 API/schema/ABI/数据格式时同步。所有旁路线不得要求 T0 集成者中断当前门。

每个硬节点结束只汇报：`x/9 → y/9`、关闭的门、耗时、artifact、下一门的 P50/P90。若 `x=y`，第一句
必须是“正式进度 +0”，随后才允许说明消除了什么 blocker。

## 责任结论

不是 125 个提交没有价值，而是我没有让它们服务于九项机器门。活动量很大、交付量几乎没动；
验收拓扑、关键路径保护、操作者判断、测试落点、估时和汇报都由我负责。后续只有机器门分子增长
才叫进度增长。
