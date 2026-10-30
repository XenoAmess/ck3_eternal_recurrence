# 本地 OpenAI 兼容模型服务作为执行者与初级工程师的可行性预研

## 2026-10-30 八M与恢复候选实际采用补记

machine_id: xenoamess-full-tower-eb9d2c1186。本轮集中调度18次真实调用的原件为 D:/ck3-state/model-dispatch65/SUMMARY.json 与 REVIEWS.json；后继HTTP统一交回 /root/model_coordinator64。继续使用8080/qwen38-coder、固定源码前缀、SSE首内容TTFT及总耗时分别记录，未据排队或耗时推断缓存命中。

实际采用有不同程度：M3两角色guard候选经隔离34项通过；M6采用两处guard，owner补signed owner投影后85项通过；M0采用角色guard、完整step parser及桥委托，owner补negativezero和可合回测试seam后默认52项通过；M7采用首轮生产片段，owner补action域与真实producer回归，248断言及完整Bridge单TU编译通过。M2经两处窄纠正完成真实四值parser/reader/submit隔离。上述初始结果均为D候选，开发源整合与部署分开记录。

失败未抹去：M7第二轮输出截断被拒；M5首请求漏max_tokens导致无界流，受控停止后改有限输出，后继CPP/ASM真实编译失败均保留，owner最终修ABI/layout使49B真实片段82项通过，不能记模型原样成功。M4夹具可编译但运行越界，owner窄修后四world通过，没有由此捏造生产缺陷。Java恢复模型测试捏造API被拒，owner实际回归另发现非FOCUS Unknown误选。Ledger模型指出重复读取但仅实例内缓存不足，跨session实现由owner补齐。

HTTP200、可解析JSON、编译、隔离行为、开发源采用逐级区分。这些源码候选调用不等于运行期游玩决策；真实qwen SELECT_PROPOSAL/ACCEPT由Game批次原件另行记账。

预研日期：2026-10-27；归档日期：2026-10-28。

用户问题：如果本地提供 OpenAI 协议的模型 HTTP 服务，能否由当前主智能体调用，承担执行者和初级工程师工作，以加速项目推进并节省 token。

结论：技术上可行，值得从一个本地执行器、小范围真实任务开始试验。主智能体负责拆任务、关键判断、复核和集成，本地模型负责边界明确的检索、分析与代码修改。当前结论来自接口和流程预研，尚未接入实际服务，没有任务成功率、加速比或节省比例的实测结果。

以下产品能力依据预研当日查询的官方文档；实际接入时仍须核对目标执行器版本及服务实现。

当前 Codex 自定义子代理继承父会话的模型 provider，不能通过子代理配置单独指定另一个本地 provider。当前会话提供的子代理接口也没有任意 HTTP 服务地址参数。因此，混合使用云端主智能体与本地模型，需要通过独立执行进程或工具调用实现。[官方子代理配置](https://learn.chatgpt.com/docs/agent-configuration/subagents)

Codex CLI 支持自定义模型服务，可以作为独立的本地执行器。预研所查配置中，`model_providers.<id>.wire_api` 唯一支持值为 `responses`；仅支持 `/v1/chat/completions` 的服务不能据此认定可直接接入 Codex CLI。Responses 兼容性还须验证工具调用、流式事件和多轮工具结果回传，普通文本请求成功不足以证明执行链兼容。[官方配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)、[自定义模型服务与本地模式](https://learn.chatgpt.com/docs/config-file/config-advanced)

模型 HTTP 服务负责推理；读文件、运行命令、修改代码和执行测试由执行器负责。工具调用循环需要把工具执行结果送回模型，再继续下一步。协议兼容与工程任务能力应分别验证。[官方工具调用流程](https://developers.openai.com/api/docs/guides/function-calling)

| 接入路径 | 适用条件 | 建议 |
| --- | --- | --- |
| 独立 Codex CLI 执行进程 | 服务兼容所需 Responses API 与工具调用链 | 优先复用，减少新增编排代码 |
| 薄的 Java 调用适配层 | 服务只有 Chat Completions，或现有执行器无法兼容 | 只实现实际缺少的调用与执行循环，可接入现有 Quarkus/MCP 宿主 |
| 一次请求返回分析或候选补丁 | 工具调用能力尚未通过验证 | 可先承担日志分析、资料整理和候选修改，实际应用与验证由主智能体完成 |

Codex CLI 的非交互模式支持 JSONL 事件输出和按 JSON Schema 请求最终结果，便于收集终态、用量和产物。第三方模型服务是否正确支持这些能力仍需实测；接收端继续做运行时校验。[官方非交互运行说明](https://learn.chatgpt.com/docs/non-interactive-mode)

对本项目，建议按下列范围试用：

| 工作 | 建议分工 |
| --- | --- |
| 编译日志归类、定义及调用方检索、证据整理 | 本地模型优先承担，保留可定位的文件与日志出处 |
| 已定位的小范围 Java 修复、回归测试补充、机械性迁移 | 本地模型执行，主智能体复核关键差异及实际结果 |
| 跨模块字段合同演进、复杂故障定位、架构取舍 | 主智能体拆分后委派局部实现，统一检查生产者与全部消费者 |
| CK3 实机操作、账本恢复、最终验收和发布 | 继续由现有权威流程负责；候选分析不授予额外提交权 |

节省云端 token 的关键是让本地执行器自行完成多轮工作：

1. 主智能体给出目标、相关输入、修改范围、依赖和实际验收命令。
2. 本地执行器自行检索、修改、增量编译和读取诊断，在同一开发目录继续修复。
3. 返回补丁、简短结论、实际命令、退出码、耗时及必要日志位置；失败和未执行项分别说明。
4. 主智能体检查关键差异、必要证据和受影响行为，完成集成与最终验收。

如果每读一个文件、每执行一条命令都由主智能体转发，委派开销会削弱收益。完整日志和源码反复回灌主上下文也会抵消节省；优先返回摘要与可查证据，复核需要时再读取具体内容。直接可由搜索、编译器或确定性脚本完成的工作，继续交给这些工具。

本地推理本身不消耗云端模型 token，但任务说明、复核和返工仍有云端消耗。本地模型也有推理 token、设备占用与运行成本，不能把云端 token 减少写成总计算量减少。

在相同任务及验收标准下，可使用下式评估：

```text
云端净节省量 = 原方案云端用量 - 混合方案全部云端用量
混合方案全部云端用量包括任务说明、协调、复核、返工和必要接管
```

输入、缓存输入和输出用量分别记录；费用或订阅额度收益按实际计量方式核实，不能仅按 token 总数推断。加速效果使用任务从开始到最终验收的完整墙钟耗时，包含本地排队、执行、复核和返工。

本地推理速度、一次成功率及与 Maven、Native、游戏进程争抢资源的程度，都会影响加速结果。增加执行器数量可能增加排队和内存压力，应按实际资源与任务独立性安排并发。

项目既有工程约束继续适用：

- 新增生产适配代码使用 Java + Maven + Quarkus，并沿用强类型合同及入口运行时校验，不新增 Python 生产编排模块。
- 复用独立开发目录、构建输出和合法缓存，先编译改动模块、受影响消费者与必要依赖，再做一次最终完整验收；不为本地执行器另建平行构建系统。
- 公共字段变化同步生产者、全部消费者、序列化和相关回归。局部编译通过不能外推全图通过，HTTP 成功不能替代 CK3 实机后态。
- 保持单一游戏动作提交权威、唯一账本 writer 和 UNKNOWN 不重放；本地模型返回的建议仍须经过既有执行链。
- 后续模型载荷、工作树、构建及日志按执行机器的获准根映射与[通用存储策略](storage-retention-policy.md)管理；并发任务避免修改同一文件或争用同一输出目录。

建议首轮选择少量已有明确验收标准的真实任务，覆盖日志分析、调用链检索、单模块修复和回归补充。记录任务通过率、云端用量、完整耗时、返工次数及本地资源峰值，再决定扩大哪些任务。先试一个本地执行器，优先复用现有工具，不把建设完整调度平台作为试验前提。

开始实际接入需要明确服务地址、模型标识、接口类型、认证方式、上下文上限与并发容量。凭据通过执行环境提供，不写入文档。当前没有已验证的模型选型、服务部署或性能结论。

## 2026-10-31 resume91：高并发、真实采用与审阅成本

machine_id: `xenoamess-full-tower-eb9d2c1186`。用户明确续行并恢复高并发模型使用；源码HTTP统一由`/root/models91`协调，运行期selector仍由runtime独占，源码候选不计游玩决策。详细逐次事实见[resume91记录](autonomous-agent-progress/2026-10-31-resume91-models.md)、D:/ck3-state/model-dispatch91/STATUS91.json与REVIEWS91.json，能力对照见[能力边界](local-model-capability-boundary-2026-10-28.md#2026-10-31-resume91方法与整图候选的实际对照)。

19:06:52.777474Z这一明确观察点已97真实任务/121HTTP尝试；82个stop/完整JSON，15个length截断。客户端POST_BEGIN→ATTEMPT_END区间峰值25；18:54:37独立服务metrics为running24/waiting0/KV57.58%。客户端区间含网络/等待，不能等同服务推理数。第三批24次首流ConnectionReset10054保留partial后按配置各重试一次；接口失败与length/语义失败分记。继续使用8080/qwen38-coder、固定三消息完整源码前缀、有限max_tokens，SSE有效content TTFT/headers/总耗时及usage分别保留；cached未报告，不从耗时推缓存或吞吐收益。

本轮已有多种真实局部采用，不能把完整JSON数当工程成功数：SEM103两行typed完整SEM parser/reference候选经actual canonical102全readSettledSameGame、529451B历史SEM transport与错Game guard2P后S/Z采用；install104 activeGame抽取及catalog末尾候选由owner补本地入口/可见性，strict2叶编译0与既有deadline4P，真实慢catalog仍由105现场检验。Family source首轮rawSHA目标有帮助但大小写错误，owner补后1P，未POST第二轮取消，不能记模型原样成功。

其它有原件的软件结果包括：Context纠错guard/fixture后28P（owner新增反控）；liege17纠错header对原118B8分支；Surrender反馈后新单方法3参数3P；converter120原样20场景100业务语义检查，另263基础设施；succession窄callback原样，owner映射/main后2case、26总检查=22语义+4身份；special三Java raw-return方法原样36断言；death图/期望/次数保留，owner仅namespace和8name后8组原278B差分及guardedcycle。Java JSON从整类真实编译失败收窄为imports/helper/2constants后原样装配，strict2source0、2P；4.306s窄响应与62.051s整类响应上下文/输出均不同，仅作事实，不据此宣称加速比或缓存收益。旧pair132本轮原样Java对原71B12270例/0差异属于旧候选新验证，不增加本轮POST。

审阅也是需要校准的工作：M2/Java JSON字符串曾被owner误读外层JSON转义，实际提取源码确认后撤回；M2因此多发的第二轮逐字无diff，不能记新修复，随后真实javac字符字面量错误才触发第三轮。Java material曾误报不存在API，逐声明确认Binding/FrameLoader/Original getters/settled都存在后撤回，最终未编拒绝原因是authority/证据closure不完整。协调者hashJava末任务叠加另一Return schema造成冲突，缺源码归封包错误，不归模型Java编译失败；新任务整份替换末消息为唯一schema。GUI02缺首轮已接受selector正文而只给无工具模型响应路径，属上下文缺口。这些成本和勘误都保留在REVIEWS，不能全算模型推理失败。

大图候选出现实质ABI/指针/返回值误读和重复imports/正文直至length；对应链在重复具体失败后由owner接管，后继只派仍未完成的typed小方法、数值reproducer或实际诊断。HTTP高并发按真实需求、队列、错误和资源滚动；未以已完成分析、无需求调用或每岗配额维持数量。没有证据支持全工程成功率、净token节省或永久能力上限。

### resume91 补记：actual105 大材料与异常类型闭环

actual105 Family链提供833行真实排名、实际preview原件与两完整消费者时，模型13完整源/31661输入token首候选9.017s返回3处最小FullJsonTree读取/去小budget全量编码修改。原样严格编译因漏2个import真实失败；owner只补import后正链通过，但必要非法UTF8/重复key负例揭示4处公开异常类型回归。第二轮5完整当前源/12554输入token、10.503s返回7个精确edit，由owner原样采入，严格编译0；同105完整Root/legality/projection/preview→lineage选择40408→diagnostic及6负向通过，既有Lineage整类10P/0skip。Diagnostic旧golden缺席未宣称整类绿。两轮与owner import成本分记，不把首轮完整JSON当首次通过，也不为普通接续增加来源门。

首轮19:13:11已传输完成但约19:16才通知owner的延迟属于协调交付，不能归HTTP慢；后继P0让结果子岗最高优先单任务SUMMARY/CONTENT直达，异常类型轮与M5 intake/propagation轮均先直接交owner再索引。M5二叶大collection入口4.043s及后继四叶传播7.288s在返回时只授完整传输；其后两轮候选经owner补import/保留historical128并实际采用五叶，传播六hunk仅CRLF适配。5叶+probe严格编译0/2.100s、Java0/1.215s；actual105材料的source-derived最小plan832852B→pool832967B→input1395039B/result565953B/selector563211B/analysis2250B及7负向/默认检查通过。旧FormalIntake整类8P4F（旧cachedpositiveID/缺golden）保持，不声称整类绿。五叶正式FF17f70beeb4；Family两叶与M5五叶共7src由runtime采用，MB106真实END0/16.667s、业务106同Game接续启动，安装/编译不授ActionSelected/receipt/新日。

基础单方法还有独立证据：NativeBridgeBuild.clean子进程env补一个flag请求925输入/249输出，1.891s完整，原样采一行；单源Java21严格编译0/10.209s，普通FF67b4a9d984，无新增镜像测试、全局环境/SDK/Game修改。这是精确代码/任务下的小修改，不是自主模块构建闭环。原件见D:/ck3-state/resume91-runtime/obligations105与D:/ck3-state/resume91-java-delivery/native-env-compile；详细结果继续由REVIEWS91归并。


### resume91 运营补记：用户更新 IP 为 192.168.1.11

2026-10-31 本地日期，用户两次明确将模型 IP 更新为 `192.168.1.11` 并要求记入运营。唯一配置现为 `http://192.168.1.11:8080/v1` / `qwen38-coder`，端口、模型、认证与稳定三消息规则保持；后续调用从配置读取，不向旧 `192.168.1.7` 发新请求/重试，也不回退 8000。Root 已更新地址迁移和 AGENTS；本岗只补真实连接观察，旧观察移入 history，旧实验保留。

新 IP 首个真实任务 `runtime-storage-hotpath108` 于 UTC `2026-10-30T20:17:28.587641Z` POST，`20:17:38.031662Z` 完整结束：HTTP200、stop、SSE DONE、JSON，headers 3.612 秒、首个有效内容 3.614 秒、总 9.444 秒，25828 input / 955 output tokens，cached tokens 未报告，客户端实际 exit0。输入为四份完整当前源 117152 字符，实际任务仅普通 storage 两方法候选；固定 system 正规化为唯一配置，原完整源和末任务未改。连接成功本身不授源码采用、测试、性能改善或 Game 信用；首答源审仅 root 分支可用，漏 lock-path 热路径，已另交真实窄纠错。

此前 `runtime-command106` 的五次 HTTP503 和最后一次 reset 归旧 IP；六次均无有效候选，不是新 IP 失败或模型推理失败。新首轮成功也不证明长期稳定、并发上限或缓存命中。原请求、SSE、结果及迁移记录在 `D:/ck3-state/model-dispatch91/runtime-storage-hotpath108/` 与 `NEW-IP-MIGRATION91.json`；运营明细见 [resume91 模型页](autonomous-agent-progress/2026-10-31-resume91-models.md)。

后继 Storage 窄纠错原件：第二轮8.943秒/481out，首答root分支与第二答lock方法两生产hunk均原语义采用，owner生产语义纠正0；三源strict javac0/3.664秒。必要测试首跑7P1F，owner修正测试清理后只重跑首失败1P/2.185秒，不能写同一JVM8P；S/Z最小采用和正式FF `2377f74ccf` 已独立回执。此结果没有量化加速，MB109实际loop与Game进展另记。


### resume91 增并发：owner 直接调用与更大真实任务

用户再次要求加大并发后，Root 于本轮20:27Z附近解除中央逐包封装/启动瓶颈：模型运营继续由 models91 归总，八M、Java与runtime的源码owner可在各自唯一task目录直接复用既有 `call91.py`；不新建平台。调用器从唯一配置读取1.11地址/固定system/model/defaults，支持已有三消息body或source_files/task_path有限spec，最后REQUEST实际包含完整当前源和唯一末任务。启动通知无需等中央ACK，终态由原owner和results91即时转交；已有EVENTS目录拒重复派发，运行决策HTTP仍由runtime独占。

UTC20:37:22.912观察：新IP客户端实际峰8（20:36:59.164561），当刻在途4；同一次有限服务metrics为running4/waiting0、KV原值0.1489899。随后20:37:31的EVENTS快照为新IP39逻辑任务/41次实际BEGIN、39END、在途2。二者采样时点不同，不能把累计、旧IP峰25或客户端区间当服务器推理并发；24–32目标尚未达到。运行留一位是调度意图，无服务端硬reserved证明。

输入/输出规模已实际扩大：queue闭包29源366020字符、105690prompt/6500out，HTTP200但length，81.093秒/TTFT19.472秒，原件不拼接；Focus MaterialSource 17完整API+7excerpt、95820prompt/1698out，完整stop54.942秒，连接完成未授编测/采用。ledger109的13完整源218436B、55611prompt/3259out，完整stop66.547秒，但首候选漏实际head/persistedHead路径，源审拒绝未编。NamedValue266B组件完整候选12015prompt/6249out、stop92.104秒，源审发现虚构字段/descriptor/RX与偏移问题，未编；后继owner固定ABI宿主，再派真实callback/case方法。大输入不是实际改写规模，完整输出不是采用，cached均未知。

新IP已确认的P0采用：canonical108两local guard删除原样采用，strict基线0P1F到必要1P/20.530秒，保真实Native过期拒绝/新鲜对照，S/Z后正式FF `9f9728ecc7`。Storage两轮各一个生产hunk原语义采用、owner生产语义改0，三源strict0/3.663884秒；首8case为7P1F，owner修测试AfterEach清理后只重跑失败1P，非同JVM8P；正式FF `2377f74ccf`。没有量化提速或新增Game日信用。原件见 `D:/ck3-state/model-dispatch91/`、各owner DELIVERY，汇总与操作入口见 [resume91模型页](autonomous-agent-progress/2026-10-31-resume91-models.md)。

后继 Army cohort04 已真实完整200/stop：52份源387857字符、116097prompt/4330out/120427total，82.321秒/TTFT14.863秒、cached未知。owner审12个实际undefined符号到producer路径及14obj模板可用，已物化D配置；编译/链接尚0，不授闭包PASS或生产采用，拒其未验证self-contained保证。源数不是改写文件数，120427接受也不是最大context声明。


### resume91 真实未解诊断的 thinking 请求观察

Root 明确授权在仍未解的M5端到端诊断上做一次单请求模式探索：`m5-end-to-end110-correct` 与 `m5-end-to-end110-thinking` 的实际三条messages逐条完全相等（稳定源475409字符、末诊断54267字符），只有 `enable_thinking=false/true` 与 `max_tokens=10000/16000` 不同；全局默认false未改。两者均真实HTTP200/stop/SSE完整、调用器实际OS0：前者113262prompt/2271out、34.852秒，后者113298prompt/2698out、39.214秒，均未触输出上限，cached未知。

逐条读取最终原SSE：889/1115个JSON记录，delta键只有role/content，未见reasoning/reasoning_content/reasoning_tokens键或content中的think标记；usage仅prompt/completion/total。只能记录“未见可见reasoning”，不能凭请求flag认定真实内部模式已启用，也不能据字段缺席认定不存在内部推理。prompt差36的原因未知；输出预算不同、时序及并发未控制，不作速度、缓存或能力因果结论，语义采用另由owner按当前源审阅。本试验没有重发已解答案或授Game信用。可复核纯事实对照为 `D:/ck3-state/model-dispatch91/THINKING110-ACTUAL-COMPARISON.json` 与 `REVIEWS91.json` 的mode_comparison，原REQUEST/SSE保留。
