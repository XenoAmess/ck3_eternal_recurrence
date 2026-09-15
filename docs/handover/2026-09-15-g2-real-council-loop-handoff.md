# G2 真实议会闭环交接

交接日期：2026-09-15（Asia/Shanghai）
交接范围：G2 整局自动游玩、当前议会闭环、相关 `open_kaishek` 合同、Git/CK3 现场
权威进度入口：[`../autonomous-agent-progress/g2-requirements-v1.json`](../autonomous-agent-progress/g2-requirements-v1.json)

## 一句话结论

整局自动游玩仍是 **1/8（12.5%）**。R693 已真实证明 exact-build、paused、application-main 条件下可读取玩家总管候选，但正式策略尚未在真实 CK3 中完成“观测 → 选择 → 任命 → 下一 paused frame 后置核验 → 下一 turn 消费”。本轮已把同帧能力数据、正式策略选择、动作核心、application-main 共享胶水、Python 正式动作链及 `open_kaishek` 被动合同全部线性推进到主线，并清理相应临时分支、clone 与构建目录。下一位应先关闭仍使 action capability 保持不广告的 production final-gate binding，再构建唯一 R694 候选。

## 进度口径与八项里程碑

不得依据能力数、测试数或模块数改写分母。权威机器合同固定为八项，当前只有 G2-M1 完成：

| 里程碑 | 名称 | 状态 | 当前主要缺口 |
|---|---|---|---|
| G2-M0 | GEN-034 three-way war exit | `in_progress` | 同帧 white-peace 比较、一次终止动作、物质后置条件与 cold restore |
| G2-M1 | entity directory and core turn bundle | `complete` | 已完成；更深派系身份与治理字段归后续里程碑 |
| G2-M2 | natural event semantic loop | `in_progress` | `tgp_travel_events.0030` 与 `death_management.1007` 的正式推荐、动作和结果链 |
| G2-M3 | succession and realm survival | `in_progress` | 一次自然死亡、继承结果核对、同一战役以真实继承人继续 |
| G2-M4 | peace governance vertical slice | `in_progress` | 议会正式闭环、建设、生活方式、封臣/派系，以及两游戏年无人点击验收 |
| G2-M5 | family, diplomacy and complete war | `not_started` | 联合候选评分、补给、盟友、战役预算与多战争协调 |
| G2-M6 | schemes, institutions and activities | `not_started` | 正式 typed state、semantic action 与结果模型 |
| G2-M7 | identity adapters and long campaign qualification | `not_started` | 政府适配、覆盖矩阵与长周期记忆校准 |

因此：单次议会查询或任命 GREEN 都不能自动把总进度改成 `2/8`。只有 G2-M4 的全部既有条件同时满足，整体才可变为 `2/8 = 25%`。

## 已取得的真实 CK3 证据

### R692：保留的 capability RED

- 封存候选：`Z:\ck3_mod_rewrite_process_assets\g2-m4-council16-r692-9cdb430`
- 结果：`unavailable/application_main_thread_required`
- 决定性计数：`last_submit_result=0`、`last_wait_result=4`、`executor_started_requests=0`
- 根因：私有 wrapper 在提交 main-thread query 后同步等待并取消，executor 尚未开始。
- 无 UI 输入、无游戏动作、无日期推进、存档未变；cleanup GREEN。
- post-run manifest SHA-256：`589FFE1526F3C98DFC5C04E5F0C8A48EC41D6DB893CC5497AE459781D4F2FFCB`

### R693：私有 reader production-live primitive GREEN

- 封存候选：`Z:\ck3_mod_rewrite_process_assets\g2-m4-council18-r693-5e0c5d5`
- 候选 manifest SHA-256：`D6789F5D9859E788F8A58B0DAB2BF8561FD347830B18683C7C26EEA791A1ADB8`
- sealed manifest SHA-256：`02B68D8B4641D698ADFE87F131A36EDCFA126EA5667AFC91CF57C9C46DE36A65`
- post-run evidence manifest SHA-256：`FC59D8D8F001B6B6F6A5ACD041EFBA78596F7D837A54819A8B3F3A2E3EAFABC4`
- exact build：CK3 `1.19.0.6`；EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- paused snapshot：`native:3`；`date_raw=53178264`；owner/player CharacterID `29829`
- 结果：`available`，11 个 native-accepted 总管候选，临时向量已释放，无 raw pointer 落盘。
- 运行保持只读：0 UI 输入、0 gameplay action、日期不推进、源/目标存档 SHA 不变。
- R693 已终止；旧轮次 R692 已终止；交接收尾时必须再次即时确认 `ck3.exe` 进程数。
- 限制：R693 没有公开 query、没有正式策略消费、没有任命动作、没有动作后置条件。

## 本轮已经合入的主仓工作

以下提交都已通过 rebase-only 线性进入远端 `master`，相应临时工作分支、clone 和构建目录已清理：

| 工作包 | 原工作 tip | 最终 master commit | 结果 |
|---|---|---|---|
| G2-R693-GREEN-REPORT | `521b2921` | `6493d2ad` | 封存 R693 证据并保持 `1/8` |
| G2-COUNCIL21 enrichment | `91b23663` + `96d41524` | `7630e623` + `79f49adf` | 现任与候选 stewardship 同帧补全；public runtime 仍待接入 |
| G2-COUNCIL20 formal strategy | `4de9387a` + `defec0fc` | `3df892ed` + `bd120e5a` | 只有 query+action 双能力时进入议会；正差值才替换；完整 CharacterID 平分 |
| G2-COUNCIL22 action core | `2d4075b9` | `c9ae3ceb` | strict request、exact helper、helper-only ACK、下一 paused frame receipt；仍 private/unadvertised |
| G2-COUNCIL24 Python action consumer | `a7756cd5` | `a7756cd5` | 正式策略到 typed native driver；ACK 只记 pending，独立后帧 receipt 与公开后帧共同确认成功 |
| G2-COUNCIL23 native shared glue | `0104b097` | `42acfb60` | application-main 邻接执行 reader/enrichment/projection/submit/receipt；生产 final gate 未绑定，保持不广告 |

`master@c9ae3ceb` 的官方 CI run `34935988818` 为 exact-head GREEN。它只证明静态工程，不替代 live 证据。之后远端 `master` 又有与本闭环无关的 CoA Pages 提交；最终交接 Git 基线见下文收尾状态。

## open_kaishek 同步状态

`open_kaishek` 已线性更新：

- `68d4191a`：Council19 结果 schema 基础。
- `38cd918b`：Council20 MCP/profile 被动合同。
- `b47f30b6`：Council21 `incumbent_main_skill` 与 readiness 修正。
- `c88206e5`：Council22 `game.action.assign-councillor-v1` 被动合同。

`c88206e5` 已进入远端 `main`；Profile API `23/23`、CK3 profile reactor `63/63` GREEN。工作分支和 clone 已删除。该兼容合同明确保持 `native advertised=false`、`MCP registered=false`、`runtime/live=false`、`formal strategy live=false`、`fallback=false`。

## 本轮最后收口的两个工作包

### G2-COUNCIL23-NATIVE-GLUE

- 原工作分支 tip：`0104b0973088e77f4c9972a63cec15a120eb6427`。
- 最终 master commit：`42acfb60a32cd6c0789f2f5c9886528e1840607c`；`git range-diff` 证明 rebase 前后补丁等价。
- 结果：一个 application-main executor 邻接执行 private read → release → enrichment → public projection，并连接动作 capture、final legality、`0x1056C00` submit 与下一 paused frame receipt；`action_request_id` 跨三个 step 保持冻结。
- 验证：Debug/Release 各 3/3 聚焦 CTest GREEN；glue fixture 5/5；source verifier normal/`-O` GREEN；Council22 exact-build ABI verifier GREEN；两种配置的 `xar_ck3_bridge` 均构建成功。
- 已知硬缺口：production replacement fireability（`CFireFromCouncilConfirmation::CanConfirm` 等价判定），以及 already-councillor、guest、pending-interaction 等 final gate 的真实 callback binding。缺口未闭合，因此 action capability 仍不注册、不广告。
- Git 现场：错误 SSH origin `XenoAmess/ck3_mod_rewrite` 无法推送；集成负责人从 clean clone 导入同一 commit，经已验证的 HTTPS 远端推送工作分支并线性集成。远端工作分支、本地 clone 与三套构建目录均已删除。

### G2-COUNCIL24-PYTHON-ACTION

- 原工作分支与最终 master commit：`a7756cd5d7b2077de51d9d182d403d6cc648f91a`。
- 结果：正式 `native_auto_run` / `ck3_auto_turn` 路径生成 strict action request；helper ACK 只进入 pending；独立 receipt 会核对 backend、query sequence、status、native/snapshot/public revision、date、owner 与 incumbent，之后 `native_auto_run` 再核对公开后帧。
- query-only、action capability 缺失或非 paused 时保持零议会动作，并继续既有 turn。
- 验证：作者聚焦测试 normal/`-O` 各 24/24 GREEN；集成者复核新增合同测试 normal/`-O` 各 6/6 GREEN；`git diff --check` GREEN。
- 状态：static-ready，未启动 CK3、未宣称 live；远端工作分支、临时集成分支、本地 clone 与跟踪引用均已删除。

## 唯一下一条执行链

接班后不要新增 native/MCP 库存。按以下顺序继续：

1. 读取本交接、`AGENTS.md`、`g2-requirements-v1.json`、`docs/ck3-native-ai/council-composition-ai.md` 与 `council-assignment-action.md`。
2. 即时核验远端 `master`、CK3 进程数、持久轮次台账和本文记录的剩余 gate；已合入的 Council23/24 临时分支与 clone 应当保持不存在。
3. 只实现 action readiness 所缺的 production final-gate callback binding：already-councillor、guest、pending interaction，以及替换路径 incumbent fireability。沿用现有 source contract、fixture 和 exact-build 绑定；未闭合前继续不注册、不广告。
4. 如果这一步改变接口、schema、版本或依赖，立即更新配对的 Python 合同与 `open_kaishek` 被动 profile；不因兼容而放宽 readiness。
5. final gate 聚焦测试通过并线性进入最新远端 `master` 后，按同样的 rebase、fast-forward push、原 tip → 最终 commit 映射和合入即清理规则收口该包。
6. 只有最终主仓 commit、DLL、Python runtime、capability manifest、存档、启动参数、断言和证据目录全部冻结后，生成唯一 R694 候选；不要沿用 R693 的旧 DLL 或 source commit。
7. 启动前取得 CK3 独占权，确认所有受管环境没有其他 CK3。新启动必须分配持久记录中的下一个单调递增轮次；若仍是 R694，则记录候选标签 → 当前轮次 R694 → 最终 commit 映射。
8. R694 必须经正式 `native_auto_run` / `ck3_auto_turn`，先查询、由策略选择、再执行任命，随后取得独立下一 paused frame incumbent 后置条件，并在下一 turn 消费结果。私有 harness 直调、人工参数或 helper 返回码都不能替代这条链。
9. 如果存档中没有空缺或没有比现任更高 stewardship 的合法候选，记录 `NO_CHANGE` 的真实消费证据，但不能把它冒充任命成功；另找符合既有合同的自然合法场景，不能在看到结果后降低门槛。
10. 议会闭环 GREEN 后继续 G2-M4 的既有建设、生活方式、封臣/派系链，并完成两游戏年无人点击验收；这之前总进度仍为 `1/8`。

## R694 最小验收门

启动前固定并逐项关闭：

- exact CK3 `1.19.0.6` 与 EXE SHA 匹配；
- 主仓 source commit、Release DLL、Python runtime source tree、候选 manifest 与 sealed manifest 都有 SHA-256；
- 只打开本次 Council production feature，其他候选开关按清单关闭；
- 公开 query 与 action capability 只在真实 runtime binding 完整时广告；
- 存档、mod/load order、`-userdir`、`-loadsave`、pipe、timeout 和 evidence 目录冻结；
- 启动前 `ck3.exe=0`，启动后唯一 PID/creation time/owner 已记录；
- 动作前 snapshot/public/native revision/date/owner/position/incumbent/candidate 同帧绑定；
- final candidate producer 重新确认 exact candidate 恰好一次，CharacterID round-trip 成立；
- replacement 必须通过真实 fireability；pending interaction 等禁止状态必须拒绝；
- ACK 只记录 helper invoked，`queue_acceptance_observed=false`；
- 下一 paused frame revision 前进、owner/task/position 一致、candidate 成为 incumbent；
- 下一正式 turn 读取 receipt/新观测，不重复提交；
- RED、timeout、证据不足与未执行分开记录；失败后不无修改重复启动；
- cleanup 证明 CK3/watchdog/helper 全部退出，源存档与需要保持只读的目标未被意外改写。

## Git 与环境注意事项

- 主工作树 `Z:\ck3_mod_rewrite` 是历史遗留的 dirty detached 工作区；不要 reset、checkout、clean 或拿它做集成。继续使用独立 clone/worktree。
- 主仓远端分支是 `master`；`open_kaishek` 远端分支是 `main`。
- 主仓禁止 merge，只能 rebase；共享 `master` 禁止强推。
- MSVC 构建要先进入 VS 18 Developer Command Prompt，并使用 VS 自带 CMake/Ninja。PATH 上的 Cygwin Ninja 会把 Windows 路径交给 `/bin/sh`，导致 `cl.exe` 路径损坏。
- exact source-contract 在独立 clone 中要显式配置：`-DXAR_CK3_EXECUTABLE_PATH="Z:\ck3_mod_rewrite\Crusader Kings III\binaries\ck3.exe"`。默认相对路径在 clone 中不存在时会产生验收环境 RED。
- 删除 Windows clone/build 前先用 Python 解析绝对路径并确认位于 `Z:\ck3_mod_rewrite_process_assets`；随后在同一 Python 进程内清除只读属性并递归删除，不跨 shell 拼接删除命令。
- 当前与 G2 无关的长期分支 `codex/mod-shiren-import` 有独有提交，不得删除或顺手集成。
- 日常验证按改动范围做聚焦测试；不要为单个 bug 无意义扩大到永久长跑或重复全量 CI。

## 最终 Git、进程与工作区状态

本节是交接提交前核验的权威现场：

- 主仓远端 `master`：`42acfb60a32cd6c0789f2f5c9886528e1840607c`（交接文档合入后，以包含本文件的最终 master commit 为准）
- 主仓本地集成 clone 的远端跟踪：`42acfb60a32cd6c0789f2f5c9886528e1840607c`
- `open_kaishek` 远端 `main`：`c88206e5e7bd00e81db973b0be498f23117ba47c`
- Council23：原 tip `0104b097` → master `42acfb60`；临时分支、clone、build、跟踪引用已清理。
- Council24：原 tip `a7756cd5` → master `a7756cd5`；临时分支、clone、跟踪引用已清理。
- 本次交接文档 commit：以本文件所在的最终 master commit 为准；工作分支 tip → master 映射见交接完成回报。
- CK3：`ck3.exe=0`，未启动新实例。
- 当前轮次：当前轮次 R693 已终止；旧轮次 R692 已终止；当前没有存活轮次。
- 当前 RED：R692 历史 capability RED 已由 R693 私有 reader GREEN 关闭；没有新增运行 RED。正式 public/strategy/action 闭环尚未执行，production final-gate binding 仍是明确验收缺口，不能称 GREEN。
- 临时资产：本任务实现分支与工作 clone 已清理；交接分支、交接 clone 和集成 clone 将随本文合入立即清理。
- 整局里程碑：`1/8 = 12.5%`。
