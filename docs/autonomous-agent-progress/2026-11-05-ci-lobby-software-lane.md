# CI lobby 软件原件入口的选择修复

官方 CI `41900511164`（a24e6d9，job126821326688）的真实失败发生在构建工具资格阶段：`Selected pinned lobby fixture inputs required`。该回执中的 `maven_result=null`，尚未开始 Maven／完整 reactor；不能把它说成新的业务 Java 或回归方法失败。

工作流已经传入 `XAR_FRONTEND_LOBBY_SOFTWARE_FRAMES`。现有 `FrontendLobbyCallbackObservationTest` 会复制4份实际 Native 序列化原件、生成当前 Java 请求，再逐份测量5个原件，构造同机器、有限复核期的严格 pinned 元数据，由原 typed reader 验证。外层 `ControlBuild.reactorVerifyArguments` 却在这个消费者运行前，一律要求另一套外部元数据三元组，因而阻断已有入口。

本次只改现有参数生成方法的一处选择：如果三个外部环境键中任意一个显式存在，哪怕为空或残缺，仍进入原严格外部校验；没有显式外部键、并且软件原件目录环境值非空时，才让已有测试自己生产并验证 pinned 元数据。缺少两个入口时仍失败。所有 metadata、byte／SHA、机器、复核期、原件、SDK、其它 target／profile、Maven执行及工作流均保留。无效的软件目录仍由实际消费者拒绝，不跳测试、不合成 Native 数据。

新增4个有限回归方法调用真实包内参数生成器：软件入口不要求外部片段；任一显式空／残缺外部键不能回退；缺失／空白软件入口仍失败；合法外部 pinned 片段保留，原件篡改仍拒绝。测试中的5份小文件只用于参数及 pin 校验，未执行 Native 语义消费者，不授 ABI 或实际游戏信用。

模型首派4份完整源427041B及4422B合同，真实200／stop，36.1342182秒、TTFT21.2928455秒，prompt99428／completion2083。owner 部分采用精确外部三键谓词与测试结构；原 diff 的上下文／计数不能直接应用，测试又误调了 private 七参重载，已机械投影为真实包内五参 API，并补 null-safe、空白及篡改断言。没有R2。生产完整 outside 逆还原一致。

本地仅持有2026-10-22旧构建工具 donor，不能拿它证明当前源码依赖匹配。没有为本单元读取实际 C、编译整工具或占用游戏／P0资源；本次新增源码及4个方法等待正式 Cloud CI 的真实首编／执行，尚未授编译、用例或 CI 通过。当前 ACK 后负 fresh READ 的实际功能修复仍优先，CI与文档不作为运行恢复前置。


后到正式 CI 终态（41920385302）：本工具组件已真实通过，build-qualified-tools receipt为PASS、Maven exit0／555.301976秒，1199方法0error／failure／skip；新增ControlBuildLobbySoftwareLaneTest明确4P／0.129秒。旧“等待CI”是发表时切点，不能覆盖本次后到实际组件资格。

整条Official仍failure：后续qualified child约1.63075秒即因 `artifacts/tools-postqualification/actual.json` 缺失，在ControlCi.runQualified1947读取前置资格文件时失败；本次未授完整reactor／实际HTTP链或wholeCI通过。不能制造该actual、跳过完整Own／原件／两个真实JUnit资格或以工具1199P代替此下游合同；后继只核已有producer／consumer的真实接线及缺输入边界，不为CI操作Game。


后到独立 Official 41922443393（010cec200f1e，2026-11-04T23:56:03Z终态）同样是工具组件通过、整链失败：qualified Tools Maven exit0／1040.4439083秒，实际1199方法0error／failure／skip，lobby新4方法通过；之后qualified child运行3.1196564秒，在相同 `ControlCi.runQualified1947` 因 `artifacts/tools-postqualification/actual.json` 缺失退出1。只下载该run唯一指定的1.10MB Java证据，没有重跑CI或本地JDK。来源为 `ci-010-terminal01/OFFICIAL-TERMINAL01.json`（4869B／64748bca…），不是新Factory、完整reactor或HTTP链通过。

有限接线审查确认：现有ControlCi.qualify构建并验证Tools后启动qualified child，但没有调用已有ToolsPostqualificationInputProducer41／postqualifyTools；runQualified首先读取上述实际资格。已有producer要求同一次完整Tools来源匹配的七类真实原件：固定完整producer源码、实际Host＋Tools materialization map、历史已完成receipt、真实historical capture、原quota lease／rejection／source map；还需要原实际bulk材料及JUnit依赖，随后实际fullOwn与两个JUnit输出才能产生actual.json。当前审查未持这些输入或该调用接线，记录为NOT_HELD，不断言世界上不存在合法原件。

合法后继只能沿现有Hosted DATA合同提供并验证这些原件及实际执行证明；不能把缺失占位、旧1199P、伪receipt／map／quota、手写PASS或跳门当成资格。精确来源清单为 `ci-cbd-terminal01/MISSING-POSTQUALIFICATION-INPUTS02.json`（四份完整Git源码对照），暂不扩大现场、上传私有原件或降低gate。两条Official各自真实失败与耗时保留，普通运行和必要功能／性能源工作继续RUNNING，不以CI作游玩前置。
