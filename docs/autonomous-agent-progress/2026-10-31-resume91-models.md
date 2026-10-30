# resume91 本地模型真实调用与能力边界

machine_id: `xenoamess-full-tower-eb9d2c1186`。源码模型 HTTP 唯一协调为 `/root/models91`；运行期决策 HTTP 由 `/root/runtime91` 独占并预留至少一个请求位。用户本次明确续行并要求高并发使用本地模型，旧休假 STOP 只作历史保存，未改写旧队列或原件。

采用 `docs/local-model-executor-config.json` 的 `8080/qwen38-coder`、固定三消息源码前缀、temperature0、thinking=false、有限 max_tokens、SSE 有效内容 TTFT/headers/总耗时/usage 分记；cached 字段未报告时保持未知。复用旧 call90.py 的维护副本 `D:/ck3-state/model-dispatch91/call91.py`，未新增调度服务。每一实际请求的完整 body 为各任务目录 `REQUEST.json`，变化任务真实位于最后消息；不是仅 POST 路径或 manifest。

## 19:06:52Z 后继观察与审阅勘误

`2026-10-30T19:06:52.777474+00:00`：97个真实任务/121次HTTP尝试均已传输终态，82个stop/完整JSON、15个length截断；客户端峰值25，发生于18:58:27.389244Z。第三批24次首流ConnectionReset10054分别保留partial并按配置退避到第2尝试，不把接口中断计推理失败。该刻服务running0/waiting0；随后立即滚动派4个仍未闭的小任务（M6 helper/core-test、M0并发source review、M3 numeric oracle），不是固定配额补位。

完整逐项审阅/归因持续写 [REVIEWS91.json](D:/ck3-state/model-dispatch91/REVIEWS91.json)。新增真实结果：M1 Context02原样guard及QueryFailure fixture在D采用、owner补反控后28P；liege17第二轮原样header strictCL0/原118B8分支通过；Surrender新方法原样严格编译0/新3参数3P；M7 special三Java raw-return方法原样严格编译0/36断言，解释metadata仍拒绝；M3 succession返工73行callback原样语义采用，owner提供映射/main后原184B2case/26检查通过。以上都是D软件范围，不能外推生产部署或Game行为。

runtime-install104完整模型候选16.634s返回：factor activeGame与catalog末尾替换被接受；owner另修factory入口和helper可见性。2叶strictjavac0/6.911s，既有PhaseDeadline4P；S/Z采用由runtime记录，慢catalog真实正向留105，不把现成4P称实机通过。初次已发请求没有后来补到的Configuration整类，这个输入事实保留；owner后续结合其operationTimeout合同审阅，无需追认补发。

审阅成本与勘误必须保留：

- M2 random-Java首轮及Java JSON纠正包的字符串曾被owner误读外层JSON转义。真实提取源码核对后撤回该缺陷；M2第二轮因此逐字无diff，虽有真实HTTP也不是新修复。M2随后实际javac44/45字符字面量失败才是另一真实返工03。Court CASE的转义缺陷同样已撤回，其余确切拒绝仍保留。
- Java material所用Binding/FrameLoader/Original getters/settled都真实存在，owner先前API发明分类已撤回。最终未编源审为INCOMPLETE_AUTHORITY_EVIDENCE：authority/journal、实际catalog/action/replay对象同一性及证据/producer closure不完整，原样0采用。不能将该项计不存在API失败。
- 协调岗将hashJava任务后再接含另一Return schema的完整诊断，造成最终输出要求冲突；缺Java源码归封包错误，不能计Java编译失败。旧REQUEST保留；Java02整份替换末消息为唯一candidate_java schema，后续length及实际错误独立评审。
- M2 GUI02稳定源缺少首轮已接受新selector正文，只给了响应路径而模型无文件工具；这是上下文设计缺口，不能据此判单语句能力上限。owner已接管，不事后重发追认。
- 旧模型pair132本轮原样Java对原71B native12270例/0差异，接受D raw predicate但拒绝其几何命名；它属于resume90旧候选的本轮验证，不加到resume91 POST数。

多个完整ASM/全图装配候选出现重复imports/正文直至length、ABI/指针和返回值错误。已在具体链重复失败后交owner接管，模型继续承担有完整声明的小方法/纯数值/实际诊断；不对已完成分析做第三次复述，也不将单项失败定为永久能力上限。静态拒绝与真实编译失败分别记录。部分较早exec session后继poll返回Unknown process id，工具OS退出码不可得，保UNKNOWN，不由HTTP SUMMARY反推exit0/1。

## 真实并发与传输观察

`2026-10-30T18:54:37.666637+00:00` 观察已实际启动 **42 个任务、42 次 HTTP 尝试**；18 个终态中12个 stop/完整 SSE/可解析 JSON、6个 length 截断。当前客户端在途24，客户端区间峰值24发生于18:53:53.998501Z。此数按本机 POST_BEGIN 至 ATTEMPT_END 区间计算，包含网络/服务等待，不能当作服务端推理数。

同次 `/metrics` 实际报告 running24、waiting0、KV57.58%；这是独立服务指标。D盘余577.23GiB、可用物理内存20.18GiB、commit余65.27GiB。运行预留保持；后续按真实服务队列、终态、错误与真实待办滚动，不设每岗调用配额。

持续机器索引：[STATUS91.json](D:/ck3-state/model-dispatch91/STATUS91.json)、[BATCH01-JOBS.json](D:/ck3-state/model-dispatch91/BATCH01-JOBS.json)、[BATCH02-JOBS.json](D:/ck3-state/model-dispatch91/BATCH02-JOBS.json)、[封包读回](D:/ck3-state/model-dispatch91/packets/PACKET-ASSEMBLY-READBACK01.json)。BATCH 是已封包清单，含未 POST/后取消意图；真实调用数仅取 EVENTS。每任务保留 REQUEST、原始 SSE、逐尝试 CONTENT/RESULT、SUMMARY；HTTP200或完整JSON均不授采用信用。

## 已收到的真实审阅与采用

| 任务 | 传输与实际审阅 | 编测/采用边界 |
| --- | --- | --- |
| runtime-sem103 | 首轮完整，headers14.445s/TTFT14.446s/总25.645s；完整SEM误用LEDGER小预算的两行typed parser/reference修复 | owner严格javac0；真实canonical102完整readSettledSameGame、529451B SEM实际transport与错Game guard 2P0F；S/Z采用，MB由runtime增编。模型源码候选不是运行期决策。 |
| runtime-obligations-source | 首轮完整且编译0，但真实测试仍0P1F：raw SHA目标正确，大小写仍错 | owner补equalsIgnoreCase后1P0F；记MODEL_ASSISTED_OWNER_CORRECTED，不能记原样通过。接管时二轮尚未POST，已取消，不计模型调用。 |
| m3-converter120 | 首轮完整，owner原样采用D方法 | 单TU compile0/run0，20 scenes、363总Check=263基础设施+100业务语义；没有Game信用。 |
| m3-filter119 | 两轮完整候选仍含布局/数组拷贝/快照别名/未初始化错误，整候选拒绝 | owner重写unsafe fixture后29 scenes、1210总Check=931基础设施/fixture+279原生语义。模型13case表可留，不能将owner绿追认为完整候选采用。 |
| m1-native-liege17 | 首轮完整；实际CL exit2/C2679：119B赋118B数组，且假造输入文件名 | 未采用；已提供真实编译诊断窄纠错。 |
| m1-context-consumer | 首轮完整但4处捏造canonical API且byte[].equals身份比较 | 实际javac失败；第二轮按真实API窄纠错。 |
| m0-queue-build-plan | 首轮完整但12 objects漏query mailbox、坏hunk抄未改C++且漏main接线 | 源审拒绝，未编测；第二轮要求四段完整小字符串而不输出整fixture。 |
| m0-core-wrapper | 首轮完整但重复allocator、违规改Mapping、fallback pair宽度/offset错误和硬写未测计数 | 源审拒绝，未编跑；保留实际同前缀纠正请求。 |
| m3-bank31 / m3-succession | 首轮分别5000/7000 length截断；另含明确ABI/dataflow与巨大重复布局错误 | 不拼接partial、不自动重试length；分别收窄五字段与<=100行回调/State返工。 |
| M5四业务体 | 12FAD50完整但callee/alias错误拒绝；其余3项6000 length | owner缩短为target stores/args数组的1500–2400预算新任务；输出控制失败与语义错误分记。 |
| M7 preload/special | preload6500 length且条件/参数错误；special完整但寄存器/返回分支错误 | 原候选均拒绝；新轮分别限五路径表与纯Java返回合同。 |

主要采用原件：[SEM103 SUMMARY](D:/ck3-state/resume91-runtime/sem103-regression/SUMMARY.json)、[Family DELIVERY](D:/ck3-state/resume91-runtime/obligations/DELIVERY.json)、[M3 religious RESULT91](D:/ck3-state/resume91-m3-native/religious91/RESULT91.json)。其它原始响应和审阅留各D独占目录；未报告的状态保持未确认，不把静默当采用。

## 本轮探索边界

当前以真实新任务并行测试：小方法修复、实际编译诊断纠错、纯数值ASM重现、单TU typed fixture、多文件consumer合同及同World HELLO/fullSnapshot装配。提供输入大小仅说明上下文，不等于实际改写规模。完整ASM ABI/内存布局重建仍由owner主导；模型负责独立可核的小段，较大候选隔离验收，不阻塞同Game接续。

尚未POST的worker launcher维护在runtime owner接管采用后取消，不能追认模型实现；已人工完成Ranking亦未重发。源码候选与运行期qwen selector分开计数，本岗没有Game动作或运行期决策HTTP。
