# CI lobby 软件原件入口的选择修复

官方 CI `41900511164`（a24e6d9，job126821326688）的真实失败发生在构建工具资格阶段：`Selected pinned lobby fixture inputs required`。该回执中的 `maven_result=null`，尚未开始 Maven／完整 reactor；不能把它说成新的业务 Java 或回归方法失败。

工作流已经传入 `XAR_FRONTEND_LOBBY_SOFTWARE_FRAMES`。现有 `FrontendLobbyCallbackObservationTest` 会复制4份实际 Native 序列化原件、生成当前 Java 请求，再逐份测量5个原件，构造同机器、有限复核期的严格 pinned 元数据，由原 typed reader 验证。外层 `ControlBuild.reactorVerifyArguments` 却在这个消费者运行前，一律要求另一套外部元数据三元组，因而阻断已有入口。

本次只改现有参数生成方法的一处选择：如果三个外部环境键中任意一个显式存在，哪怕为空或残缺，仍进入原严格外部校验；没有显式外部键、并且软件原件目录环境值非空时，才让已有测试自己生产并验证 pinned 元数据。缺少两个入口时仍失败。所有 metadata、byte／SHA、机器、复核期、原件、SDK、其它 target／profile、Maven执行及工作流均保留。无效的软件目录仍由实际消费者拒绝，不跳测试、不合成 Native 数据。

新增4个有限回归方法调用真实包内参数生成器：软件入口不要求外部片段；任一显式空／残缺外部键不能回退；缺失／空白软件入口仍失败；合法外部 pinned 片段保留，原件篡改仍拒绝。测试中的5份小文件只用于参数及 pin 校验，未执行 Native 语义消费者，不授 ABI 或实际游戏信用。

模型首派4份完整源427041B及4422B合同，真实200／stop，36.1342182秒、TTFT21.2928455秒，prompt99428／completion2083。owner 部分采用精确外部三键谓词与测试结构；原 diff 的上下文／计数不能直接应用，测试又误调了 private 七参重载，已机械投影为真实包内五参 API，并补 null-safe、空白及篡改断言。没有R2。生产完整 outside 逆还原一致。

本地仅持有2026-10-22旧构建工具 donor，不能拿它证明当前源码依赖匹配。没有为本单元读取实际 C、编译整工具或占用游戏／P0资源；本次新增源码及4个方法等待正式 Cloud CI 的真实首编／执行，尚未授编译、用例或 CI 通过。当前 ACK 后负 fresh READ 的实际功能修复仍优先，CI与文档不作为运行恢复前置。
