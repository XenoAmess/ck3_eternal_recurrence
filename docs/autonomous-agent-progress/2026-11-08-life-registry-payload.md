# P106：大 Life 请求的技术能力表投影

本单元继续真实性能主线，目标仍为端到端10秒/新增确认保存日。以下为离线纯DATA格式化结果，不授当前局恢复、HTTP模型延迟或实际保存收益；P100原拒绝链、UNKNOWN、Guard、账本、旧期限和冻结工作树边界保持。

## 已确认瓶颈

原e79b `REQUEST.json` 为2784926B，SHA `d5ba35a419234e9393ad94436c1ec8559bed7d2c941cc06cf277e80c968ea994`。从原BATCH29 `last_plan` 取得33个真实visit，从已qualified Driver1475取前139个原history行，保留10项全部导出action facts、原command及过期deadline。旧wire的63个 `OperationKey[value=...]` 名按明确历史格式还原；未导出的fact origin/evidence用显式formatter-only绑定，不冒充原内部对象、Root权威或新许可。

唯一Java探针于2026-11-07T18:36:14.758440Z关闭资源：两个实际资格均true，当前P105 `tryCompactPayload` 返回null，实际完整wire1537575B。独立完整任务oracle user59757B、policy920B，最终wire65913B，比原65536门多377B。hello的134个text能力与observations集合完全相同，6个Life依赖均真实advertised。仅投影该重复技术表、计入新增声明与policy的prospective wire为60559B。此前旧请求的额外压缩不能计入P106。

探针原件：`D:/ck3-state/resume91-native-integration/p106-life-probe01/ACTUAL-P106-SINGLE-FORMATTER-PROBE.json`（13141B，SHA `3141fd7c39fc58d853b21b99d911b7793e1815eecd6642617ab25c1066d815a6`）。该次formatter-and-qualifier计时含两个predicate、requestPayload及额外独立compact调用，不是exclusive formatter耗时。

## 实际生产改动

只在原完整compact wire超限后验证hello能力表全text、与observations集合一致并含required Life依赖，再在当前调用的私有输出树中替换该数组为有序6项，添加 `hello_capabilities_projection=required_life_action_subset/v1` 及明确policy。原small分支先返回，字节不变；未知形状、不匹配、缺依赖或投影后仍过大均保留原generic fallback。65536门、完整current facts/unknown diagnostics、原proposal、trace导出项、facts、stop intent、原command SHA和期限不变。

本地模型仅一次真实源码候选，UTC18:39:06.684至18:39:15.229，200/stop，TTFT3336.89ms、total8545.50ms、prompt24006/output841、cached=null。核心分支partial采用；owner简化Set/List和命名，不把HTTP成功算软件通过。原件位于 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/large-life-model-payload106/model01`。

必要Selector单生产TU已exit0/4class/6.9278569秒，outer全窗7.6080298秒，18:42:19.547408Z实际close/held=false。未重编旧P105 baseline、Council或旧测试；编译通过不授装载或运行行为。

## 新DATA与失败原件

唯一新Test源覆盖三个方法：真实大输入的完整独立wire oracle及原输入/command不变；原small profile字节早返（故意不匹配registry仍沿原行为）；不匹配、nontext、未知形状、缺依赖和其余当前事实仍太大的full fallback。实际首轮2P/1F，额外诊断仍1F；两次失败均为owner把prospective候选的全wire SHA误当跨JVM固定值，未据此改生产代码或直接替换hash。

独立完整oracle与actual60559B逐字一致。Root精确diff确认只有原AdvancePlan.capJson使用Map.of所致 `/bounded_stop_intent/advance_plan/campaign_deadline` 八个成员顺序跨JVM变化，其他键、类型、值及数字token均不变。最终以本JVM独立完整oracle严格byte比较，并每次测量核本JVM的hash/length；原失败方法最后1P，另外两个既有新绿不重跑。三新方法均已通过；同一个新Test源因必要诊断/合同修正共有三次编译，不写成一次全三绿。原RED、原始XML及关闭资源回执完整保留。

精确差异原件：`D:/ck3-state/resume91-root/post-vacation-20261107/P106-CROSS-JVM-WIRE-ORDER-DIFF.json`（1522B，SHA `a05268b63af6dea5cec8ff1e81532846e8faaeada6d0e6300528ef5950053309`）。原小压缩request146574B、batch10632B作为可复现测试资源；Driver1475.gz沿用既有application test-jar资源。

## 实际有限同输入测量

测量fixture按DriverObservationAssembler及RootPlanningInputsFactory同一originalRow生产规则补回numeric native history139行，计入P104两条路径原有完整编码比较成本。未知原成员位置明确标为DATA reconstruction variant，不追认为缺失的内部FullSnapshot原字节；两模式用同一变体、原command SHA和期限。

旧P105已编Selector为A，新P106已编Selector为B，只切有序classpath中的Selector前缀，不重编旧源码；固定A0/B0/B1/A1四个JVM，统一CPU1/384MiB/45秒，每个2warm+4measure。全部8warm及16measure保留，无强制GC、删慢样本或速度断言。每模式8个实际测量：

| 本地完整requestPayload组件 | A | B |
| --- | ---: | ---: |
| wire bytes | 1537575 | 60559 |
| 中位耗时ms | 140.26505 | 47.0638495 |
| 全部测量范围ms | 109.9269–171.098999 | 43.5004–52.5756 |
| 均值ms | 141.813125 | 47.86178725 |
| 主线程实际分配中位bytes | 192894264 | 61160740 |
| 两次完整process合计秒 | 14.1102789 | 13.1112573 |

该组件中位耗时约减少66.45%，主线程分配约减少68.29%，wire减少96.06%。计时含完整requestPayload、初次超限compact编码及之后成功投影；load、独立oracle setup、main及outer process另记，不把组件差异授整个进程、HTTP/TTFT、模型选择或游戏日提速。baseline两JVM原1c1e7c0f全wire marker均实际通过；candidate两JVM各自原始SHA与完整独立oracle相符，跨JVM的上述成员序变体分别保留。

末个ABBA资源于2026-11-07T19:07:14.448230Z实际关闭。全部raw样本：`D:/ck3-state/resume91-native-integration/p106-life-test03/ALL-ABBA-SAMPLES.json`（25343B，SHA `6b31c8430ddfb47bd5fe300e62b7ab0f0e53a967834e0fc5ec4593004da8184c`）。Root另独读四次ACTUAL/CLOSE与全部raw，摘要 `D:/ck3-state/resume91-root/post-vacation-20261107/P106-ACTUAL-ABBA-REVIEW.json`（7051B，SHA `a6998fa87a683270b3619e742287d2eb06cc187ac2c529c6cbaaa1c817a65f7f`）。

下一P107为普通融资Gap/Emergency/Loan角色的大snapshot输入问题，生产单TU已独立green，新公共接线DATA继续；其cash/focus完整Construction链仍另计。P108已确证原cash normalize的重复大snapshot encode/parse，接在P107之后。连续性能主线保持，实际保存日新增0，10秒目标尚未通过。
