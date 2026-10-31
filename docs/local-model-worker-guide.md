# 本地模型：跨机器 worker 使用与实际经验

更新：2026-10-31。所有机器的 worker 共用本指南和 [唯一配置](local-model-executor-config.json)；不以旧交接中的地址、机器名或 D 盘路径配置新任务。用户已明确授权持续高并发使用本地模型，并要求继续探索能力边界。

## 连接与跨机器使用

| 项目 | 当前值 |
| --- | --- |
| OpenAI 兼容 base URL | `http://192.168.1.11:8080/v1` |
| 源码候选接口 | `POST /chat/completions`，流式 SSE |
| 模型别名 | `qwen38-coder` |
| 认证 | 无需密钥；客户端强制要求 API key 时填 `local` |
| 旧地址 | 不自动回退 `192.168.1.7` 或 `8000` 端口 |

接手时读取配置及本指南，使用已安装的 HTTP 工具或兼容客户端即可，不需要本机的 `D:/ck3-state/model-dispatch91/call91.py`。该脚本是一次执行机器的既有维护调用器路径，不是跨机器依赖，也不是新 worker 的必备入口。

日志、候选、构建输出使用**执行机器自己的**获准数据根和真实 `machine_id`。不要照搬另一机器的盘符、解释器、Maven 绝对路径、证据路径或 Game PID。运行期决策由该场游戏的唯一运行 owner 装配；源码 worker 的模型调用不能修改另一机器的运行账本或提交游戏动作。

只有需要排查连接时才做一次列表读取，不为每个任务增加探测前置。以下单行命令可由 CMD 或 POSIX shell 执行：

```text
curl --connect-timeout 10 --max-time 30 --fail-with-body --silent --show-error --noproxy 192.168.1.11 http://192.168.1.11:8080/v1/models
```

本机 `xenoamess-full-tower-eb9d2c1186` 于 2026-10-31 02:32Z 实际执行上述命令，退出 0，返回中包含 `qwen38-coder`。这是本机连通事实，尚未代替其他机器实测。其他机器需能路由到这个局域网地址；连接失败应检查其路由、代理和服务状态，不改用旧地址。服务列出的 `max_model_len=1048576` 是服务宣告，不是已验证的复杂任务能力上限。

## 请求布局与最小调用

先选真实尚未完成、能独立验收的任务。默认先让模型提出实现，再由 owner 审阅和编测；不要先写完整答案，再让模型复述。

请求始终使用配置里的实际 `model`、`defaults` 和**逐字固定**的 `prompting.system_template`。按顺序提供三条消息：

1. `system`：配置中的固定系统模板。
2. `user`：确定顺序的当前完整合同、相关生产者/消费者和目标源码。实际源码变化时正常更新，不为缓存保留旧代码。
3. `user`：变化的真实任务、实际诊断、输出约定和返工要求。

使用有限 `max_tokens`，启用 `stream=true` 和 `stream_options.include_usage=true`。既有维护调用器接受 `1..16000` 的输出预算；这是调用器约束，不是模型输出能力结论。按任务给够输出空间，优先精确方法或最小 hunk，避免要求重复整份长源码。默认 `temperature=0`、`chat_template_kwargs.enable_thinking=false`、`response_format.type=json_object`，具体值读取配置。

`request.json` 必须由 worker 用**真实源码和真实待办**生成，不提交含占位符的演示请求。一个 JSON 输出约定即可；不要把 `source="completeJava"`、`source="completecpp"` 这种示例放进任务，模型曾直接照抄它们，而没有输出源码。返回值中只有代码路径、但没有文件内容，也不能替代给无工具模型的实际上下文。

在已经选择好的任务数据目录内，有真实 `request.json` 时，以下是一轮实际请求的通用命令：

```text
curl --connect-timeout 10 --max-time 900 --fail-with-body --silent --show-error --no-buffer --noproxy 192.168.1.11 -H "Content-Type: application/json" --data-binary @request.json --dump-header ATTEMPT1-HEADERS.txt --output ATTEMPT1-RESPONSE.sse http://192.168.1.11:8080/v1/chat/completions
```

这条命令只保存一次传输。已有客户端应继续负责事件、重试、有效 content TTFT、usage 和候选审阅，不必为此新建调度平台。不要只看 curl 退出码或 HTTP 200：还需完整 SSE 终止、`finish_reason`、可解析的候选内容；`length` 和半截流不能采用。工具调用曾因服务缺少 tool parser 返回 HTTP 400；先使用已可用的普通 Chat Completions，不把接口配置问题当成推理能力不合格。

## 高并发规则

- 具备完整输入的源码 owner **直接并行派发**，不等中央逐单封包、ACK、整波完成或结果汇总。运营协调负责记录和调节，不能成为每次 POST 的串行门。
- 准备下一项真实方法、候选审阅和必要编测，与其他完整独立任务的 HTTP 重叠。共享编译读窗只暂停受影响的源码写入或编测，不暂停独立模型 HTTP。
- 以 **12–16 个真实在途请求为初始目标**；有真实积压和服务余量时继续增加。按实际服务 running/waiting、错误、KV 占用和延迟调整。这是运营目标，不是已达事实，也不是已经实现的分布式调度器；多机不能各自把目标写成已达全局并发。
- 一个任务内部有不同且独立的实现、消费者或必要 probe 时，可以提供各自完整上下文同时派发。保源码写权和输出目录互斥，不用多个模型无协调地改同一叶。
- 不设每岗刷调用配额，不重投已完成工作，不为数量制造总结或重复绿测。输入尚缺时明确具体缺口，改派其他真正有输入的工作。

经验：曾因准备、审阅和下一包衔接串行造成服务空闲。02:10:10–02:20:10 UTC 冻结窗口是27次POST、窗口峰4，当时新IP历史峰8；后继07:39:58.637575–07:40:02.177609Z实际新峰14，仅3.540034秒。09:01:31Z新快照服务/客户端均0在途，最近10分钟28次POST、窗口峰5，仍未持续达到12–16。累计调用和短峰都不能掩盖空档，也不能据此认定服务容量上限；旧地址峰25不混入新IP实测。后继改为提前取得具名源码、由独立owner直接POST，并清除已经实际解除的旧编译HOLD；无需为恢复HTTP等待编译槽。

## 传输重试与记录

读取配置中的 `transient_retries`：最多 6 次尝试；瞬时 429/502/503/504、连接拒绝/重置、连接或读取超时、流不完整，按 `10/20/40/60/60` 秒并加配置抖动退避。等待期间推进其他独立工作。永久请求、schema 或认证错误先修请求，不盲重试。

保留每次完整请求、开始/结束事件、响应 headers、原始 SSE、有效正文、用量、错误和最终审阅。半截流保留为失败原件，**丢弃该候选并重发完整请求**，不能拼接两次响应。重试范围仅为模型 HTTP，绝不据此重放游戏或 Native 动作。

分别记录：headers 延迟、首个**非空有效 content delta** 的 TTFT、总耗时、服务实际返回的 prompt/completion/total tokens，以及可见 cached tokens。不能把 headers 或 curl 的首字节时间称为内容 TTFT。缺失缓存数据保持 unknown/null，不从排队、TTFT 或总耗时反推缓存命中；客户端 POST 区间与服务端实际推理数也分开。

## 最近实际经验与能力边界

| 真实工作 | 可复用经验 | 已验证范围 |
| --- | --- | --- |
| 模型输入无损候选别名 | 两候选数组只有在非空且结构严格相等时才用可重建别名；保未知字段、整数精度、顺序及原命令 SHA。真实 compiler 诊断能帮助模型补精确 API/cast | 实际 833 行整 DATA 可重建，已正式采用并运行装载；不是可随意删 proof 的许可 |
| Marriage 完整材料角色 | 新增明确 16MiB 角色入口并传播全部 7 个消费者，保原默认小预算和输出约束；不要抬全局上限掩盖角色错位 | 最终源码原样采用，严格编译和两必要测试通过；307352B 是软件材料，不冒充批次127未知原件 |
| M4 真实原码组合 | 模型能承担明确 API 的 producer、consumer、局部组件；完整 ABI/重定位/端口组合常需 owner 修正，必须保留各自责任 | 10RF/64例/33549完整Row40槽首次 Native→Java差分0；不外推真实allocator/CRT/EH或Game |
| M3 copy/release 边 | 小 callee 仍可能有对象 slot 转移、虚调用和 fresh load；不能凭名字生成 memcpy | 221B原码的新11例差分通过，保未知自然caller/vptr，模型首稿拒绝及owner补Hook分记 |
| 字符串与测试材料 | 提取 JSON 返回的源码后再判断转义；样本尺寸实测后再断言超过阈值 | 曾有 owner 转义误疑撤回，以及样本107352B未达262144B的真实模型错误；不能混算 |
| 参数与推理模式 | 看实际发出的 REQUEST，而不是输入 spec 或意图。旧 minimal-spec 不转发 frequency_penalty；full-body 路径可携带实际参数 | 旧0.3试验未发生；10:24Z的一次full-body 0.3确实发送但源码被拒。11:02Z新ABI请求实际enable_thinking=true并完整stop，无独立reasoning字段或服务模式生效证据；这些均无单变量A/B，不宣称参数改善 |
| 历史代码身份与原件DATA | 源码候选必须区分历史implementation/decoder/verifier文件元数据和实际不可变业务原件；删除用户已取消的代码身份审计时，检查同方法相邻live/archive代码pin，不能只删首个报错等式 | Root152模型正确给archive hunk、漏live loop由owner补；单源strict通过并发表，实跑确实越过此门，后继另一独立消费者失败，不授整链恢复 |
| 多文件权限与冷回放 | 提供实际issuer、消费者、预留/提交顺序和共享状态迁移；只编两个消费者、只测cursor DATA，不代表完整私有token与真正writer reducer已接受 | 5份取消源码候选因真实source回调/普通Running语义/冷回放/API不足拒绝；owner2源strict与实际385原件3项cursor测试通过，后继仍由运行岗补真正reservation reducer |
| 重复输出与虚构API | 完整API仍可能被忽略；检测到重复import、自我反驳填满reason或虚构构造器，整份拒绝。缩小具体未闭方法/返回范围，必要时owner接管，不把增加输出预算当必然修复 | 实际测试6000截断，缩成3case后stop却仍造API；另2份26k/25k输入的跨源审阅也length。是这些提示/任务的失败记录，不是上下文大小或推理能力的通用上限 |

给模型完整 API、输入角色、实际诊断和明确验收标准，但不要把 owner 已写好的目标实现夹在提示里。多轮发明 API 或语义错误后，由 owner 接管该整段实现，另选真正未写、可独立验收的较窄方法继续探索；不是永久把模型限定为机械修改。更难任务隔离执行，不把能力探索设成当前游戏推进的前置。

输入文件数、字符和 token **不等于** 实际改写规模。分别记录模型轮数、提示程度、原样/修正/拒绝、owner 错误和返工、真实编译与行为结果、正式采用和运行装载。HTTP成功、JSON完整、严格编译、软件测试、正式提交、Native部署、实际运行决策、APPLIED与游戏日是不同事实，不能互相替代。

详细历史与逐阶段经验见 [可行性记录](local-model-executor-feasibility-2026-10-28.md)、[能力边界记录](local-model-capability-boundary-2026-10-28.md)和[当前运营页](autonomous-agent-progress/2026-10-31-resume91-models.md)。历史证据中的机器本地路径只标识原执行现场，其他 worker 不需要先取得那些文件才能使用服务。


## 后继实测：2026-10-31 07:40 UTC 并发峰值

前文02:32连通与02:10–02:20窗口保留当时事实。本机源码请求在07:39:58.637575–07:40:02.177609 UTC首次达到新地址客户端在途峰14，持续3.540034秒。固定07:30:27.462103–07:40:27.462103窗口内，至少12在途共9.803132秒，十分钟平均在途2.0054；这是短暂达到12–16初始目标的峰值，尚未持续达到。

07:40:27单刻实际源码在途10、服务running10/waiting0、KV占用0.2853535。客户端峰14包含连接及服务等待，不能说服务同时推理峰14；也不据此推缓存命中、能力或容量上限。继续让完整真实任务的owner直接派发，准备、审阅、编测与下一独立任务重叠；有真实积压和服务余量再增加，不为维持数字重投旧绿。运行期决策HTTP另计。后继数据见[运营页](autonomous-agent-progress/2026-10-31-resume91-models.md)。


## 2026-10-31 09:52Z：外部日志目录与服务计数

worker 使用独立输出目录时，在直接派发的同时报告真实 task ID 和完整输出根；不等待运营 ACK。优先使用本机约定的标准任务根；确需外根时，运营只增加现有事件索引的精确路径，不移动原始 SSE，不重发请求。其他机器沿用自己的获准根，不照搬本机盘符。

本次发现六个已执行任务的外根尚未入索引。逐份读取原始 BEGIN/END 后，09:45:30Z 的本机在途由已登记的 0 补为 2，09:49:55Z 由 2 补为 4，分别与当时服务 running 2/4 相符；09:52:19Z 均已结束。旧快照保留，后到原件另作更正，不能回填成当时已知。服务 metrics 覆盖全服务，本机事件读取与 metrics GET 也不是原子快照；发现差异先核实际输出路径和时间，不直接宣称他机流量、服务故障或新的容量上限。新增指针和监控读取均不算模型 POST，也不授源码采用或行为通过。

## 2026-10-31 10:14Z：缩小资源暂停范围，验证实际消费者

编译和大规模I/O的暂停不应自动冻结所有模型输入准备。对已点名、边界明确、几百字节的现有callee，可进行一次轻量精确读取，然后把真实未写生产方法、消费者和必要新用例并行派发；不必等整组编译或运营ACK。重编、provider、全PE导出、共享输出和游戏操作继续服从各自owner的真实资源与写入约束。记录实际开始与结束，收到新的具体资源冲突再调整范围，不按过期HOLD空等。

实测反例：10:09:26Z观察前十分钟虽有19POST/19END、客户端峰5，采样本机与服务均已空闲；这仍未持续达到高并发目标。根因之一是小原件准备被编译HOLD挡住。随后M4/M7针对明确缺失的短callee继续真实取源与新实现派发。这项调整不增加虚构任务，不重投旧绿，不把准备包计为POST，也不把某次客户端峰值写成服务容量上限。

新增消费者适配须明确记录是在前置完整集合还是逐项消费中执行。Root的Driver无row任务两轮模型都误用逐项循环中的父级直接continue，未先验证完整canonical子项，还跳过已有row冲突；两份均拒绝，owner只接管该生产leaf。实际source合同验证复用一次，缺row豁免与已有row校验分开；软件测试由另一个真实任务模型先行。输入约53k token并不保证输出考虑集合顺序，这只说明这两次提示与答复的失败，不能推成模型能力的通用上限。

## 2026-10-31 11:38Z：让模型先推导合同，保留真实失败归因

原生方法任务可先给完整具名原件、实际调用点的寄存器/栈前后值及相关类型，让模型提出ABI和typed API；owner先核对会影响调用者的宽度、返回值、地址、flags与opaque边界，再并行派发尚未写的方法、消费者和独立见证。不要先由云写好目标算法，也不要把未经核实的API直接传播到整组任务。真实案例中SETNE被误解为CF、JB错沿前一寄存器值、CALL-site RSP与callee-entry RSP混淆；另一次owner漏给仍存活的完整RAX后，模型按错误接口生成消费者，责任属于输入合同而不能追认为模型语义错误。

不以原件字节数给能力定上限：95B方法与消费者最终模型原样候选通过有限验证，193B合同两轮完整stop仍有语义错误，7B reader也曾首轮错RVA后纠正。先保实际请求、完整答复和具体诊断，再作有限窄纠错；重复整类/虚构API/length不能拼片段采用，多轮无效后owner接管该段并派下一真实未闭任务。enable_thinking=true表示请求确实携带该设置，缺少服务端模式与reasoning证据时不称已经启用内部推理或证明能力改善。

JSON业务相等与原件字节保管分开。实际历史回放中Map.of迭代次序令同一evidence对象从reference/kind变为kind/reference，字段值未变却触发消费者重编码字节比较；根因不是浮点损失或byte[]引用相等。窄消费者应使用完整typed Source或完整Obj结构相等，保数组次序、所有字段和数值token；原始ExactRef、长度、SHA和不可变DATA读取照旧，不因结构相等放松原件保管，也不全局改serializer。两份模型分析未定位真实机制并发明API，拒绝与owner实际原件差分分别记录。

## 2026-10-31：墙钟重置与较大组合任务


有限传输观察：固定 UTC `[06:30,12:30)`、当前新地址、标准一级任务根中，共35次10054/reset失败；34次落在分钟除以10余8的第10–11秒，另一次09:08:09.955545Z。请求已运行时长为0.117682–132.356721秒（中位10.834317），不能当作统一的单请求超时。它只显示墙钟相关性，服务、代理、网络根因仍未知。保留每次失败并按原六次瞬时退避重发完整HTTP，不拼半截流、不因这项相关性改业务时限或重放游戏动作。筛选口径及两份实际EVENTS路径见[有限原始观察](autonomous-agent-progress/2026-10-31-resume91-models.md#resume91-墙钟对齐的连接重置有限观察2026-10-31-1234z)；其它机器不必取得本机D盘文件才能使用服务。

较大真实任务也继续交给模型。M5完整4798B正常路径在各组件首验后，模型提出了整段主链与具体消费者，owner仅修少量observer/Memory参数；三新生产源严格编译、首次8个完整软件组合用例通过。这里复用已有分区和已核typed API，证明的是这些组合方法，并非模型独立重写全部4798B原码或真实Native/Game验收；用例的tag2/普通fallback没有走到M0/M1两下层的四个调用边，后继另做真实双组件接线。填写实际改动规模、提示程度和未覆盖路径，不能用上下文总量、整段名称或绿例数推整体能力。对下一真实原件/API与必要独立casehost，使用已有空闲helper并行准备，各owner直接POST，让主实现审阅与后继请求重叠；不以配额或重复旧绿凑并发。

## 2026-10-31：运行中的 Family 与真实调用入口

跨文件任务须提供静态 actions/archived 列表、运行时安装的 Family，以及当前 catalog 的实际选择入口。真实 ARM 已有 Native 成功 ACK 和独立 Status，历史材料仍报 ORIGINAL_COMPATIBLE_RESULT_ABSENT；根因是材料消费者只查固定安装列表，漏掉已安装的 ARM/CANCEL Family。修复复用 actualFamily、原安装对象与实际 effect/replay/metadata，保留独立 READ；不能按 operation 字符串前缀泛准入，也不能把“兼容结果缺失”直接归成 Native 未执行。单源 strict 和12项真实 DATA/软件检查通过后，worker172同Game恢复到普通循环；这不代表后续日期已推进。

实际命令按 write、ACK、独立读回、reconciliation、父终态分别记录。gen2 CANCEL 曾真实写入并收到 native_ok，普通 Driver 就绪条件却挡住其独立 Status，途中产生 UNKNOWN；后继既有只读恢复最终将该 CANCEL 及父动作结算为控制已应用，父语义为 initialization_cancelled、三项游戏进展信用均 false。不能把途中 UNKNOWN 当最后状态，也不能因为读回失败重发已写命令；修正读取角色时还须保留真实 factual 合同，不能把无 factual 的 physical 结果伪装成完整结果。现场最终事实见[运行记录](autonomous-agent-progress/2026-10-31-java-g2-resume91-current.md)。

必要回归的输入可达性先按原件核实。M1新消费者任务曾要求零长度 inline 输入到达 hash，但真实父函数会先走 fallback；这是 owner 的任务输入错误。后继改用可达的一字节 tail 与四字节 block 两条新场景，生产接线与首次软件消费通过。提供了当前目标实现的用例请求应记为实现可见的回归候选；字面预期仍须独立核原件，不能运行目标倒产 expected 或称成盲推 oracle。

性能候选先限定真实调用范围。单份线程样本的 elapsed/CPU 不足以归因整个 worker 耗时；模型曾给出错误次数、错误 pin 复用语义，owner也曾把真实存在的 API 误判成虚构，均按原声明更正并分别记责。正式库已有 CachedHistory/refreshHead 向 S 传播的两文件候选通过严格编译和一次既有冷重读回归，保留 S 的原件验证；它是既有机制传播，没有实测加速比，不重复提交已有正式代码。另一实际 preceding 路径的新候选只在同次 preceding 查询中复用已完整验证的 receipts 列表，仍须自身行为回归，不能把按不同 ID 缓存却继续反复全量读取当作已消除重复工作。

## 2026-10-31：中断请求、输出隔离与并发统计

每个独立任务使用自己的请求、响应和事件目录；并行请求不能共用调用器的公共根。一次真实 owner 参数错误把两个并行请求写到公共根，导致 REQUEST 损坏、第一份方法正文丢失，只有最后一份消费者正文幸存。原始碰撞文件保留，丢失答复不能计采用；未完成的方法另用唯一目录重新请求。现有本机调用器已针对这项实际故障，在读请求和发送 HTTP 前拒绝把其公共根当输出目录；其它机器采用自己的目录隔离，不需要本机路径，也不增加中央 ACK。

未闭合的 POST 日志不自动等于仍在推理。两份请求被外层执行中断后留下 POST/FIRST_CONTENT，却没有 ATTEMPT_END，原 SSE 也没有完整终止、finish 或可解析 JSON；后继实际进程读回确认调用器已不存在。保留这些原件并单列中断，不能伪造结束时刻、把半截候选拼接采用，或把它们永久计为当前并发。需要恢复的真实未完成任务按原半截流规则重发完整请求到新唯一目录；已完整结束的候选直接审阅。

有限观察仍需区分峰值和持续使用。2026-10-31 14:30:18Z 快照前十分钟有57次真实 POST、57次 END，客户端峰12只持续两段、共13.776843秒；当时可核在途2，随后服务 running2/waiting0、KV约4.545%。这些是分阶段非原子观察，不代表已持续达到12–16，更不把累计请求或遗留日志算作当前活跃。原始统计中两个旧中断日志造成的“4在途”已明确剔出当前事实；细节见[当轮运营记录](autonomous-agent-progress/2026-10-31-resume91-models.md)。

## 2026-10-31：按请求尝试保留活性，提供继承 API

中断观察须作用于实际输出目录、task、attempt及原 POST。按整个task最后一条事件判断，会在新attempt2到来时把旧中断attempt1重新计活；按task永久排除又会吞掉新的真实请求。同task在其它目录的END也不能关闭本目录请求。保原始未闭计数、实际END和未知结束时间；caller缺席只能形成观察上界，不得伪造终态。现有本机reader已经按这个合同传播到当前列表、各endpoint和区间消费者；该修复的10个数据边界实际通过，未为每个POST增加进程探测或中央ACK。

局部候选与必要回归分开验收。本次reader首个整份模型修改因提前使用变量、跨task匹配和漏时间条件审拒；收窄到纯函数后partial采用，owner仍修路径等式、异常范围和装配。独立回归两份模型输出分别截断、又发明ast.compile且写错时间与预期，均拒绝，由owner完成实际10例。完整stop和声称通过都不是验证结果，也不据此给模型设通用能力上限。提供Java接口时，把继承的实际父接口方法一并给齐；一次M7首包漏给父Memory声明已明确归owner上下文成本，不能算模型凭空忽略完整API。

## 2026-10-31：原生观察域与回值之外的语义

给原生方法和消费者派发任务时，先明确当前Java类型保留了哪些可观察量。M3真实14B方法的无调用分支保留incoming RAX；现有M4共享Free83是void/int的效果投影，不能在新long接口里随手补0或从int恢复未知高32位。可以在明确的void观察域复用已有效果组件，同时把不支持的动态target和未知scalar如实表示；不能为复用方便把unsupported当正常执行或自动回退重放。同一实际研究中，模型虽正确指出信息丢失，又误把HeapFree非零写成失败、建议heap0时抛错或跳过；这些具体方案均拒绝。核对原source的分支方向、fresh read时点、cell写入与零扩展，避免按函数名字或BOOL直觉生成行为。

复杂候选反复失败后，保留失败并缩到真正尚未写的新方法，不重复派发已闭实现。M3完整Native host、纠正host和机器字节spy三稿都拒绝，owner接管设施；后继给完整新API与原58B、仅交未写Dispatch方法，337token候选原样通过首次1TU编译和4个新受控原码差分。这里证明的是该调度方法，不能说模型生成了整个host、独立重建了ABI，或证明全部机器码任务不行。对后继effects-only消费者给了很强的逐条source合同，也须如实记提示程度；输入21文件和输出完整class，不等于独立完成21文件的改写。仅有源码和stop时仍标source-ready，真实编验后再提升采用等级。[M3实际记录](autonomous-agent-progress/2026-10-31-resume91-m3.md)保留本轮来源。

返回值没有被消费，也不代表调用没有语义。一次历史读取候选把Head版换成State版，完整缓存合同追读发现：Head的once会在当前Session验证canonical DATA pins，State只精确读取anchor/target；跨Session复用的cachedHead尚未完成前者，两者不能直接称等价。该单行候选在完整源审后拒绝，0采用/0编测，owner先前过早接受也已撤回。评估替换时同时核对实际读取、会话与缓存作用域，以及调用的副作用；不从丢弃返回值或严格编译通过推出行为等价。

## 2026-10-31 16:00Z：ABI、实际 caller 与有限采用的后继经验

ABI 答对不能替后继实现或独立 literal 预授正确。M0 同一原28B initializer 首 ABI 答对 full RAX/只改 AL，但两份 witness 与窄 corebook 后来仍把非零返回误作原 handle 或整1；这些 expected 整拒，owner 接管。真实 core02 原样算法经5生产源 strict、9新 Java 场、4原码场与20个双方共同观测字段差分0后，仅授该有限组件。原 GetProcessHeap raw64 写入 global 与 SETNE AL 后 raw RAX 要分别保留；Native 未观测硬件写次数、自然 caller/当前 Game heap 未知，不能由两端返回一致补这些信用。16个真实 task、source/采用/拒绝分别见执行机 `heap-global-init176/MODEL-COHORT16.json` 和 `DELIVERY176.json`；输入文件数或 token 数不是实际改写规模。

消费 wrapper 是否压入返回地址，要读这次真实 caller。旧 manager 在 opaque port 前没有 push，旧 adapter 因而补；Header178 和 M5 新外层 caller 已写原 CALL 槽，沿旧模板再写会重复 callback。M1 Wait179 在发 consumer 请求前纠正 owner 任务，模型算法保留、仅 imports/public 机械修后，新 Header→Wait 严格组合 trace 首次通过；M5 也将其重复写明确记为 owner task 错后删除。分别冻结 physical VA、metadata RVA、call-site RSP 与 callee post-push RSP；不能套前一 wrapper 或因两个同值写最终内存一致就漏记额外副作用。

完整源码前缀还须包含真正用到的祖接口与重载。C179 首20源仍漏 ActionPorts/Receipt/State/CompositeExecution 等6 API，首稿缺方法/错 referenceOf 重载不归为完整上下文能力失败；补齐后只模型纠正 Primitive/LifeReplay 两叶，首叶执行算法原样、后叶 owner 补 exact receipt/body/唯一成员与实际 source 角色。其余3叶 owner 实现；5叶 strict0仅授可编，不授 cold watch、Native/Game 或整5叶模型采用。两轮后不把坏 whole 稿剪成全包成功；实际 REQUEST、源审、owner 改动、必要首次行为回执继续分记。

## 2026-10-31 resume91 后继：有界补丁、任务角色与约束词

机械迁移优先返回有界 exact edit 列表或小 patch；完整当前源码作为输入，不表示必须重吐所有未变文件。M0 九叶 namespace 迁移仅23处 package/import 编辑原样采用并首次 strict0；M3 七份测试42.8KB要求整源回传，12000输出 token 后 length/145.209秒整拒，owner 词法迁移并保原 literal/expected，未拼截断稿或为已闭业务重发。这两单不建立通用速度优势、文件数或复杂度上限。

源码包提供真正祖接口后，还要明确本任务接收者的 fully qualified 类型、允许的方法与目标产物角色；同一祖源文件中的无关 Calls 不是可借 API。M1 Registry182 首 consumer 借错祖 Calls，明确实际两方法后才可用。M2 207 独立 casebook 的完整 stop 纠稿却返回生产类，整拒未编；源码审阅须核类名/角色与实际调用目标，不能由 JSON/stop/可编推 witness 覆盖。所有十六进制提示加 `0x`；M1 185 原 `S-48` 与意图 `S-0x48` 的歧义归 owner 输入成本。结构化纯 DATA fixture 仍只是后继可试的真实任务方案，未实测为有效规则。

把“允许”与“必须”逐项对照原约束，并保至少一个不同合法分支的正例。SAVE181 新 Fresh 规则允许同 snapshot ID，但模型误写必须同 ID；owner 纠正，新增 probe 同时核同 ID/新 ID 正例与非法分支。该26项只授软件合同；probe 的伪 Map cast、跳过负例、非法 SHA/不合法 revision fixture 也先由 owner 修，不能把最终绿追授原整 Test。短 x64 或小 API 仍需审 SBB/EAX、LEA/CMOVE、RIP resolved RVA 和实际 CALL/RET；独立 source literal、owner 提示或已读 target 后的 oracle 强度须分别说清，不把软件场景冒原 Native/Game。

补丁包装和字节身份单独记录。无 EOF 换行的叶必须保正确 `\ No newline at end of file`，防止 `}---`/`}diff` 黏住下一 header；`git apply` 成功后仍核目标 Git blob。Windows `write_text` 默认换行转换及 `core.autocrlf` 可令工作树 raw SHA 与逻辑 LF/Git blob 不同；分别记录实际 `read_bytes()` 哈希、规范化文本哈希和编译输入，不能把 LF 预写文本哈希误标 raw SHA，也不据换行差异授算法失败。M2 十叶包装修复和本岗 SAVE181 READY 元数据误标均归 owner，原记录/勘误保留，未为此重跑绿或新发 HTTP。
