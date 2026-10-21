# 自动游玩实机前置验收整改

`machine_id: xenoamess-full-tower-eb9d2c1186`

整改依据：用户于 2026-10-21 明确指出“实机运行前的前置验收检查明显不足”，要求反思、制定方案并落地。本文负责区分已完成的修复、必须补齐的门禁及真实验收结果；检查通过数量不能代替实际调用链覆盖。

## 责任与根因

主要责任在执行者的工程组织和验收设计。旧场次的路径、退出条件及字段假设进入了通用续局代码；测试侧重函数和源码结构，未充分执行最终生成入口及其下游消费者；并行修改缺少统一的合同和集成收口。我又把分段 PASS 当成了启动准备充分的证据，使实机承担了发现基础接线错误的职责。

整改初版也暴露了同一类漏检：14 项回归通过后，新冻结目录 N25 的公共 prepare 仍因实际归档大字段的长度校验失败。历史 runner 已执行，但没有覆盖随后真正消费归档的 preflight。此次强制离线门禁阻止了 Prepared 生成和游戏启动；不能把“被门禁成功拦下”写成“整改初版已经验收通过”。最终验收必须包含同一公共 prepare 的完整落盘链。

此外，A23 的原生 SEM 返回 complete 后，客户端后验已经失败。我没有先检查队列的失败标记便提交 CAP，造成一次无效的本地拒绝。没有发生第二次 CAP 原生调用，但这仍是执行错误，需要由工具强制阻止，不能只靠操作者记住。

## 已核实的现场边界

以下仅适用于上述机器；其他机器不得据此追认安装、Steam 状态或实机资格。

| 观察时间（UTC） | 事实 | 证据 |
| --- | --- | --- |
| 2026-10-21 08:54:38 | A23 SEM11373 原生结果 complete、日期为 53279256；随后评分消费者因缺少 `campaign-score` 映射，误进入仅允许 1066 开局的建锚路径并抛错 | `runtime-a23/ROOT-FIRST-QUEUE-EXCEPTION-P37C23.json`、原 SEM 回执 |
| 2026-10-21 08:55:00 | CAP11374 被客户端前置条件拒绝，没有发生 CAP RPC；原 SEM、INFLIGHT 和异常仍保留 | `runtime-a23/p37-responses/11374-1-result.json` |
| 2026-10-21 08:59:52 | A23 已闭场：SDK queue/application 退出码分别为 1/0，Game 为强制清理退出 1、Job 最终为 0。不得写成正常退出 | `runtime-a23/ROOT-FRESH-SUPERVISOR-CLOSED-C23-A15.json` |
| 2026-10-21 09:35:24 | 第一批五文件修复已提交并推送 `361c341c2f2fd4bab393abe655208f5abcef13f3`；这不等于本整改门禁已经完成 | `source32-clock-prep01/ROOT-PUBLIC-CURRENT-SAVED-SCORE-EPOCH-FIX-FIVE-DELIVERED01.json` |
| 2026-10-21 09:42:05 | A24 未启动 Game、SDK 或 Windows Task；395 执行授权未消费，screen125 已释放 | `current-saved-a24-runtime-prep01/ROOT-A24-NO-GAME-PREFLIGHT-REMEDIATION-DEFERRED01.json` |
| 2026-10-21 11:15–11:16 | N25 实际 157 文件、评分映射、新进程消费者及历史 runner 已通过；随后 preflight 将 75964 字符的队列归档字段交给 32768 字符通用校验器而失败。Prepared 未生成，没有启动 Game/SDK/Task 或发出 RPC | `current-saved-preflight-remediation01/ROOT-A25-PHYSICAL-PREFLIGHT-QUALIFICATION01.json` |

上述相对路径以 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/` 下的 campaign 或 prepare 目录为来源，精确路径、字节数和 SHA 以原回执为准。它们不是跨机器路径配置。

原存档的业务进度仍为 5143 个已结算周期、5622/10950 天；A23、A24 没有新增游戏天数。新闭场资料如实保留 Driver history5895、原 checkpoint history5894 及 NEXT11375，新增历史只有成功的冷恢复记录。原存档、评分锚点、起始墙钟及未知请求10565的历史不重写。G2、1秒/日和30年目标不能由本整改或 CI 通过抵扣。

## 失败与必须覆盖的回归

| 已知问题 | 原先漏检的位置 | 必须执行的验证 |
| --- | --- | --- |
| 生成代码导入覆盖了 `digest(Path)` | 检查了模板，未执行最终生成模块的实际 Path 调用 | 新进程加载最终生成模块并执行原始前置路径；重名导入负例必须拒绝 |
| 新 attempt 错误派生自己的空 STATE/profile；不可变历史引用被重定向 | 原前缀止于 ADMITTED，未覆盖其后的原始环境消费者 | 原 `make_spec` → `verify_cold_profile`，核对共享 STATE、环境、历史引用及真实文件身份 |
| 漏建评分目录映射 | 文件图和哈希检查忽略非文件目录依赖；首次真实 SEM 后验才调用评分消费者 | 实际目录 same-FileID 校验，加保留 SEM 输入经过原 `check_after` → `observe_semantic` 的离线回放 |
| 缩进 JSON 与模型 canonical 编码字节不同 | 同内存测试未覆盖真实持久化和独立解码 | 保留 ExactRef 原字节/SHA 校验后，在约定 JSON 类型域比较；格式变化通过，字段或类型变化拒绝 |
| warm loader 误用关闭时的旧 Driver 身份 | 只测底层 validator，没测公开 loader 在 SDK 持久化后的行为 | 公开 warm loader 接受合法的新身份；公开 cold loader 仍拒绝关闭资料漂移 |
| SEM 原生完成但客户端后验失败后仍可能继续发请求 | 将原生结果与整个请求成功混为一谈；冷启动分支可能提前返回绕过 HALT 检查 | 真实请求入口上，后验失败后 CAP、新序号 SEM、AUTO/FULL 均不得新增 RPC，也不得覆盖原回执或清除 HALT |
| 冻结入口仍把工作区路径当作唯一执行来源 | 在工作区内导入通过，换成最终冻结目录便被同一守卫拒绝 | 新进程只从冻结目录导入，核对原来源与冻结副本的精确复制关系，执行完整验收入口 |
| 请求放行凭据可再次使用或复制 | 单次成功未覆盖重复调用和复制凭据 | 凭据绑定具体队列、进程及一次逻辑请求；复制、过期或完成后复用在传输前拒绝，原只读加载分支每次继续等待另核原始 unavailable 回执 |
| 合法的原生 FILETIME 被安全整数范围误拒 | 模拟数据较小，没有使用真实 uint64 进程出生时间 | 对历史 Python 精确整数先验证 uint64，再转规范十进制字符串；拒绝 bool、float、越界及跨 JavaScript 舍入值 |
| 请求直接写入最终收件箱 | 单线程写后读回没有覆盖并发轮询 | 在同目录写完并同步临时文件后，以拒绝覆盖的原子操作发布；发布前最终文件必须不可见 |
| 检查标签齐全却没有绑定实际消费者 | 六个检查项可以复用无关函数的结果 | 每项绑定本 Quote 对应的唯一源码、实际函数及预期观测；无关函数、别场报告或缺失执行结果均拒绝 |
| 每批 FULL 误把初始 checkpoint 当作永远不变的文件 | 只验证首次 warm，没有覆盖原生 SAVE 合法覆盖后的第二批 | 冷启动和首次 warm 保留原身份守卫；后续只接受同 Game/SDK、原 Queue 已完成 SAVE 后验和当前 checkpoint 证明的延续，失败或未知 SAVE 不获准入 |
| 历史归档的大字段被通用短文本校验器误拒 | 真实 runner 与最终归档消费者使用不同校验路径；未覆盖公共 prepare 后半段 | 专用强类型解码边界校验精确字段、规范 base64、压缩与解压上限、EOF/尾部、原始长度及 SHA；真实归档必须经过实际 preflight 校验，再实际执行全新冻结目录的完整公共 prepare |

## 两段强制门禁

第一段在 Game 启动前执行。公共准备与启动入口必须消费同一强类型合同，并重新核对当前输入。缺报告、错字段、错类型、过期、来源漂移、目录映射缺失或任何必需检查未执行，均拒绝启动；不能靠手填 `GREEN` 或外部容量授权代替。

第二段在只读实机续接后执行。离线检查不能证明未来 Native 返回、地图加载或实际录制结果。SEM 的原生结果、客户端后验和队列状态必须全部成功才准入 CAP；CAP 后验、同 Game/SDK 身份、checkpoint、BOUND 和公开 warm loader 全部成功后，才允许首 FULL。失败保持原请求身份和未知结果，不清标记、不自动重发、不建立新信用。

| 门禁 | 入口必须验证的内容 | 放行边界 |
| --- | --- | --- |
| G1 输入与序列化 | 真实 producer → 持久化 → 新进程 parser/consumer；schema、必填/可空、整数拒 bool/float、64位十进制字符串、JSON 往返 | 只允许继续准备材料 |
| G2 完整材料与目录 | 最终生成文件、原始构造器、来源闭包、SPEC、metadata、saved basis；非文件依赖和实际目录身份 | 只允许进入启动检查 |
| G3 启动环境 | 最终 supervisor 的原始前缀及 ADMITTED 后只读加载链；STATE/profile、环境、Native 参数、不可变引用和评分映射 | 完成启动环境检查；仍须其余软件门禁及新鲜 Steam 离线准入 |
| G4 生成入口 | 对最终 SDK/MCP 的实际 AST 导入段、来源守卫和 factory 参数链执行检查；执行真实参数解析及纯配置构造。仅 Native driver 构造点使用有类型的替身，不执行顶层 main 或启动管道 | 只证明软件接线；真实 Native 构造与连接留在 G5/G6 |
| G5 SEM 后验 | 原 startup readiness → 原 `check_after` → 原评分消费者；HALT、失败标记和未决请求守卫 | 仅允许下一次 CAP |
| G6 CAP 与 warm | 原 CAP 后验、原生恢复、同进程绑定、checkpoint、真实 BOUND、公开 warm loader 新身份校验 | 才取得业务准入 |
| G7 首 FULL | 原 feeder qualify、实际 NEXT、MAP/录制 session/opening 与 BOUND 一致、有限批次和容量 | 才允许首批自动决策 |
| G8 全程绑定 | 各入口复核同一 machine/runtime/basis/source/storage 合同；缺失或漂移立即拒绝 | 不提供绕过开关或旧字段别名 |

## 实施与验收方式

主线程负责合同整合、启动边界、CI、本文和最终发布；实现线程负责公共 preflight、必要入口接线与回归；独立审核线程负责核对覆盖矩阵和绕过路径。各线程拥有明确的文件范围，最终只由主线程提交和启动。并行工作不能替代统一的生产者—消费者验收。

新增、修改的公共函数必须明确参数和返回类型。结构使用共享 dataclass/TypedDict 与 Literal 状态；动态原生/生成代码边界集中校验，不能用 Any、未经验证的 cast 或成片 ignore 压过错误。精确文件回执与内部模型分别验证，不能用 JSON 表现差异掩盖内容变化。

完成标准是：公共启动路径实际挂载门禁；每个已知失败有经过真实入口的回归；负例能在边界之前拒绝，且 Game/RPC 调用计数为零；真实 SEM 后验失败后不增加任何后续调用；实际静态检查和选中的 CI 用例通过。skip、未执行项、软件资格、只读实机资格及业务结果分别报告。

这项整改未完成前，不开启下一场实机来探测上述基础接线错误。Steam 确认继续使用后台原生查询，过期回执不延用，不抢焦点或截图。

## 已落实与实际验收

公共实现为 `tools/g2_saved_campaign/current_saved_campaign_preflight_v1.py`。生产器、原 supervisor 的实际启动守卫和请求入口已接入同一合同：公共 `prepare_current_saved_offline_v1` 执行物理材料与评分映射检查、新进程冻结消费者、真实历史回放及 preflight，最后才发布 Prepared；`verify_current_saved_supervisor_attempt_v1` 重新验证完整绑定。没有绕过开关。实时 SEM/CAP/warm 门禁继续独立执行，离线 Prepared 不授予 FULL。

最终源码的 15 项整改回归全部通过、0 跳过；8 模块 `mypy --strict --strict-equality` 通过。另按 CI 中完全相同的命令执行真实 SDK 持久化与 SAVE 后续批用例：1 项通过、0 跳过。实际归档经过专用解码器、原历史回放及真正的 preflight 归档消费者；覆盖 12 份真实 payload、16 个畸形输入和旧 32K 限制的拒绝复现。独占夹具峰值397312 B，最终不存在。CI 已接入这两条测试命令及 8 模块类型检查；远程结果只按本次新提交的实际 run 回读，不用旧提交的 GREEN 替代。

| 本机观察时间（UTC） | 实际结果与证据 |
| --- | --- |
| 2026-10-21 11:25 | 最终 8 模块严格检查：`ROOT-WHOLE8-STRICT-ARCHIVE-FIX01.json`，4754 B，SHA `e317a13d2ffe09e0fcf411265924cd281c70994428e782783bf4eb504065c9f2`；续批 CI 原命令：`ROOT-CONTINUATION-CI-COMMAND-ARCHIVE-FIX01.json`，1587 B，SHA `ce7bea830c7777306ff2bcda1d2ebb8290a6f5355a2789b9801a012dab86b5de`。两件位于 `current-saved-preflight-remediation01/` |
| 2026-10-21 11:29:26 | 新 N26 实际公共 prepare 全链通过：157 文件、59 项来源闭包、8 个 canonical 入口、真实评分目录 same-FileID；消费者 proof、历史 proof 和 preflight 均先于 Prepared 发布。preflight 8331 B，SHA `67e9c0e4c29ed4bef8573cbf6015b104e25f07f725c8c91097a77268e7e6d3f2`；Prepared 2201 B，SHA `6892107f70b9dae4070304f28eb079eb95907535f657f141029d4cc06920606e` |
| 2026-10-21 11:30:11 | 再用全新 `-I` 进程执行原 supervisor 中的实际验证 Call AST；原 owner verifier 通过，10 个 tools 模块实际来源均在 N26，包含机器身份 provider。汇总 `current-saved-a26-runtime-prep01/ROOT-A26-PHYSICAL-PREFLIGHT-QUALIFICATION01.json`，5763 B，SHA `31ae524ee69da58087993cd22d7d8fffbd6dc7f3f66939e39e6c45d34b032eca` |

独立审核线程随后只读核对实际 bundle，确认全部引用、nonce、冻结 identity/core 和原启动入口的强制调用一致，未见剩余 P0；未重复测试或读取 Driver/SAVE 大体。记录为 `current-saved-preflight-remediation01/ROOT-INDEPENDENT-PREFLIGHT-REVIEW01.json`，1354 B，SHA `ac1a2460680eddd79fec7cd53e9f4570dac56b71b960dabee207de59534e2712`。

最终汇总同时保留一项执行者操作错误：第一次适配 N26 命令时，过宽文本替换把 `sha256` 误改成 `sha266`，在任何写入前被拒绝；改成精确路径替换后才执行唯一物理写入。不能删除这个失败或声称第一条命令通过。

本轮 Game、SDK、Task 和 RPC 均为零，游戏天数与周期信用均为零；`fresh_native_qualification=false`、`full_loop_permitted=false`。上述结果证明整改后的完整软件接线；未来实际游戏仍须新鲜后台 Steam 离线回执、现场资源准入及 G5–G8 的原生结果和后验，不能沿用过期状态或越过未知动作。
