# 事件后处理的两组上下文记录写入

两个实际下游现已闭合到各自函数体：`373A0F0` 是完整 **313 B** 的按键更新／追加；`373A430` 的 **535 B** 按键更新含两个数组的记录，追加和扩容路径还调用下层 helper。这里确认的是上下文记录写入，尚无具体选项业务类型或独立游戏后态。

`machine_id: xenoamess-full-tower-eb9d2c1186`；读回源审 `2026-10-26T00:23:48.818083+00:00`。目标 1.20.0.4／build25734779，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本岗没有直接读 EXE，也没有 Game、SDK、编译或测试执行。

## 原件和增量取证

本轮仅新增 batch08 index13：`D:/ck3-state/ck3-java-g2-native-static-resume61/batch08/capture01/window-013.raw`，535 B / SHA `fcf4d2e3b242d9d04f544a3c69d6f7d65f63c8a48a9707b3cf6258db0dabbf14`。正式 `resume61/b64_execution/BATCH08-RESULT01.json` 为14852 B / SHA `57d5803fb12857f3b3fdaa805de650c1bb2aedbb228118a391a025b4171c0d81`。本岗实际读回相符，完整解码至 `373A646 RET`，所有本地直接跳转均落在所读指令边界内。三个执行 phase 的退出码／Job0／守卫、inputCLOSED 以采集者原件为准，不把整个 batch 字节数算成本岗成本。

313 B 则复用原102 B和211 B缓存，没有新采、复制或制造拼接 raw。两份原件 SHA 分别为 `2d0552949d946aa73bf51494fc5e47b66072f1cb8116f0f39fd7d4bc0fef5f2f`、`522d0af63084a0d4ce5f202fff3afef489ae25633372135c5c79171f26eba0ff`；RAM 拼接 SHA `aa928500bf9fffff7821912e036246d132fe53b290a02379079b665cd56996ed`、97条指令、三个RET，均与既有 `religion-context-hostility-conversion-12004-operands.json` 的 `logical_function_closure/3` 相符。该304560 B／SHA `dedc93e8890efee26005a6ca79df51434803d561c9f8a66028bbc319ee0ffdef` 原文顶层明确目标build／EXE，`native_capture_cost/source_reads/64`、`/82` 对应两个区间。采集者复用表 `HELD-SOURCE-REUSE08-02.json` 为5016 B／SHA `64e7a33cc9e89b5d52e0cdcf4013e2338570c85a45f592817f8cdcbaa2542d63`。旧采集机器仍为 unknown，不是本轮 installed／Loaded 证据。

[上一页](event-option-postprocess-records-12004-20261026.md)在00:09记录的旧前段来源缺口，由这次找到的原manifest及续段收窄；历史页及其哈希保持原样。

## 实际调用和分支

`373B610` 将原context+0x18、行首int32 key、行+8 payload传给第一函数。它扫描24 B条目：命中只覆写+8的16 B payload；未命中且count不等于capacity时追加key／payload并count++；相等时按增长计算经allocator虚调用分配、复制旧24 B条目、将旧buffer交给其虚表+0x10，再发布新base／count／capacity。后一个虚调用的完整回收语义和allocator具体类型尚未独立证明。局部返回分别在 `373A140`、`373A213`、`373A228`。

`373B64C` 将原context和80 B行传给第二函数。它扫描context+0x100的72 B条目，以来源行+8的int32与目标条目+8比较。命中后处理如下：

| 来源／目标偏移 | 实际动作 |
| --- | --- |
| +0x10 | 两个容器地址不同才重置目标count，经`EC5460`处理容量，再按16 B元素复制 |
| +0x28 | 两个容器地址不同才重置目标count，经`9D0F30`处理容量，再将count*4字节交`4226860`复制 |
| +0x40／+0x44 | 覆写int32／单byte |

未命中且有容量时，调用 `37297F0` 写新槽，再count++；满容量则先经allocator分配72 B*新capacity，对新槽调用同一函数，对原条目逐个调用 `37295B0`，最后将新buffer／count／capacity交 `DBDB80`。这些是实际调用参数与顺序，尚未读完下层helper，不能断言其完整复制、析构或异常语义。命中分支不复制来源+0x48标记；它不是GUI选项enabled。

两组记录来自前页同一局部集合，当前源码没有供应具体虚表执行目标、真实非空记录或业务字段名。不能由上下文内存写入推断钱包、债务、关系、选项效果已完成，更不能授UNKNOWN重投。正式原件表和显式未知边见[plan](research/event-option-context-record-writes-12004-20261026.plan.json)及[生成图](research/event-option-context-record-writes-12004-20261026.graph.md)；结构／哈希检查不验证人工语义。
