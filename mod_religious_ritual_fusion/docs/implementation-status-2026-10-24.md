# 首轮编码结果：0.1.0 开发候选

本工作包先提交[编码方案](implementation-plan-2026-10-24.md)和[测试验收方案](test-acceptance-plan-2026-10-24.md)，再实现两模式主链。方案提交为 `85905d4ced48e59f826aa6bb92245af7dd1ea5d9`。当前交付范围为离线可构建的开发候选，尚未取得 CK3 业务通过资格，也未发布 Workshop。

## 已实现

- 同 Faith 礼仪融合、不同 Faith 宗教融合的目标决策，以及独立三栏对照窗口。支持核心切换、按教义组单选、知识和不可用提示、费用预览、取消及结果历史。
- 两来源的实际核心组成候选池；最终恰好三个不同核心，双方各有独有贡献。原版选择条件由源绑定目录生成，并针对最终组合重新求值。
- 两模式共用提交入口。提交时重验来源、内容、资格和费用，创建新 Rite；宗教模式再分离新 Faith。读回实际对象、核心和教义后收费、设冷却并让创始者采用。部分或未知结果进入 unresolved，保留实际引用，禁止重放；诊断窗口可隐藏和重开。
- 结果 Rite 保存双方 Rite、创建时 Faith、模式、创始者及所选核心／教义。当前默认费用为 500／1000 虔诚，成功后十年冷却；AI 首期不开启。
- Java 21 + Maven + Quarkus CLI 提供目录生成、内容校验、显式 staging 构建和逐文件核验。运行模组不依赖 Java 服务。专用 GitHub Actions 已接入完整 Maven verify，本记录不把新增 workflow 等同于远端 CI 已通过。

源绑定目录包含 157 个原版文件的 SHA、49 个教义组、97 个信条及 126 个教义。21 项定义存在静态不可用原因；Faith／Rite 锁还按模式处理。当前目录未出现因无法投影而禁用的定义，这不构成其他游戏版本或其他 mod 内容的支持声明。正式载荷清单为 67 文件，不含 docs、Java 工具、catalog、测试夹具或 target。

## 已执行验证

机器 `4-8e1c2f1861` 于 `2026-10-24T15:33:49Z` 完成以下命令，退出码 0，耗时 17.841 秒：

```text
mvn --batch-mode --no-transfer-progress -f mod_religious_ritual_fusion/tools/pom.xml verify
```

结果为 **9 tests，0 failures，0 errors，0 skipped**，覆盖严格 JSON、真实目录到消费者与 staging 的闭环、模式锁、候选自排除及苦行信条最终组合互斥。编译目标 Java 21，实际启用 `-Xlint:all -Werror`。完整模块通过不外推为 CK3 解析或业务通过。

同机 `2026-10-24T15:30:57Z` 再读命令行默认 Maven 为 3.10.0，实际 home 为 `C:/apache-maven-3.9.16`，来源 `where mvn` 为该目录下的 `bin/mvn` 与 `bin/mvn.cmd`；目录名不能代替版本读回。实际 JVM 为 GraalVM Community 25.0.4.1。这些是机器和时间绑定的环境事实，生产命令只使用默认 `mvn`。

固定提交 staging、独立 verify 和 open_kaishek parser 的实际结果在后续[静态验收回执](evidence/implementation-static-2026-10-24.json)中记录；未生成回执前不将其计为通过。

## 已落实的原生语义

详细原生证据见[接口切片](evidence/implementation-native-contracts-2026-10-24.json)。`every_rite_tenet` 缺省枚举当前 Rite 核心，不能用按母 Faith 主礼仪过滤的 `status=core` 来收集分歧礼仪独有核心。投影原版 `can_pick` 时，候选先从最终本地列表中自排除，再检验并恢复，避免它与自身产生唯一性冲突；四项苦行互斥条件针对最终核心列表检查。没有注册的 `clear_list` 不使用，沿用原版逐项移出列表方式。

## 实机待验

尚未启动 CK3，未部署或加载本产品。L1–L3 及 RRF-01～12 均未执行，包括 `Scope.TenetType`／`Scope.DoctrineType` 的实际 GUI 绑定、原生日志、真实三核心／新 Faith、一次收费、拒绝与重复提交、原版改宗近亲连带及保存冷重载。产品尚未接入公共验收入口的业务 fixture／adapter；下一工作包应先建立该入口，再按验收方案执行，不能以脚本结构或 Java 测试补填业务 PASS。

本轮未操作 Steam 在线状态、游戏窗口或账号会话。产物、来源和容量复核以带机器 ID 的静态回执为准。未执行发布或缓存验收。
