# Java / G2 R3 恢复进度

本轮由用户于 2026-10-24 重新授权接续；目标是完成 Python 能力迁移后用 Java 完整规划器继续自动游玩，同时完成 G2 M0–M7 原生研究与 Java 落地。旧 R2 STOP 和失败回执保持原状，新执行不复活旧 spec。

`machine_id: xenoamess-full-tower-eb9d2c1186`。本次进度读回截止 `2026-10-23T22:37:27Z`，北京时间 10 月 24 日 06:37；来源为 Root 本轮工具结果及下列原件。只适用于该执行机器。

## 并发与职责

恢复初始注册表只有 Root；按 [R3 团队合同](2026-10-24-java-g2-resume56-r3-team.md)复建 R2 的 56 个职责，实际注册表曾确认 56/56 子任务全部 running（另有 Root）。同一现存任务线程在新独立工作出现时复用；源码交付后没有独立下一项的线程释放槽位，不用重复扫描维持 running。此数字不代表 56 个成果已通过，或持续恒定并发。

工具/来源图/Planner/Reference/完整 CI/Root 汇线分别有唯一 owner，八 M 各有研究 owner。Root 是唯一构建、Game 和真实 writer 调度者；预算 owner 是唯一额度 issuer。公共合同协商唯一所有者，子任务先交隔离源码与回归，不各自启动 Maven。实际公共路由与领域能力的迁移对照正在重建，源码文件数不是完成分母。

## 已实际执行

默认 `mvn -version` 实际报告 Maven 3.10.0、Maven home `C:/apache-maven`、Java 21.0.10。该 home 是本机观察，不是执行规范；后续仍调用默认 `mvn`。

以下终态均为 outer exit 0、child exit 0、Job active processes 0、stop reason null，input precheck/postcheck 与 runtime postcheck 全部 MATCH。统一原件根为：

`D:/codex-ck3-demos/2026-10-22-java-phase1/build/resume-current-20261024-r3/g2-m4/tools_c15/`

| run / 原件 | 实际结果 | 证明范围 |
| --- | --- | --- |
| `raw04-compile01/terminal.json` | PASS，child 1.5107254 s | 两源码严格 javac，无新 reactor |
| `c17-source01/terminal.json` | PASS，child 5.3057069 s | 207 源码物化；未 Maven C17 |
| `raw04-run01/actual.json` | 四命名 case 全 PASS；3 个负例正确拒绝 | 原 79061 B Maven 日志解析：35 项，17 success / 4 failure / 14 skipped；原 reactor 仍 RED |
| `c18-source01/terminal.json` | PASS，child 4.1975828 s | 213 源码物化，含迁层合同与真实 child Job reader 修复；未资格化 C18 runtime |

C18 实际源图：`D:/codex-ck3-demos/2026-10-24-sharedwire-tools172-source18-r3/SOURCE-MAP01.json`，370129 B，SHA-256 `3963c70a6e0d9d63d457431b3ffc8f194050e29a09cda02fe37db149a2b9e3a0`。为了避免重复构建，C17 只作 source-only 祖先，后继只对 C18 完整 Maven、打包和 own-archive 验证。

## 源码交付及待验边界

源码工作根：`D:/codex-ck3-demos/2026-10-22-java-phase1/scratch/resume-current-20261024-r3/<owner>/`。旧 N24/N23 和冻结 runtime 只读；当前仓库 `java/` 不代表全部外置后继已集成。

SourceGraph 已交独立最终视图迁层合同源码；第二 Full35 输入锁定旧兼容切片、四组编译修复、Army collector provider、新 ClockStatus 引用、SDK05 和 Sway 遮蔽修复。81 个迁层包含 35 baseline 和 7 historical 来源；新输入尚不是 qualified Plan。Family14、NEXT/首 SAVE、FileWitness 等跨消费者 breaking 变更先闭合完整 feature 后进入下一图，不让本次编译追逐不断变化的源码。

八 M 均继续研究和 Java 增量：M3 纠正实际 succession assembler 并确认 Any 路径为 MOVE；M4 闭 TTL cleanup/rebase 来源并落 clock 投影；M5 确认候选 local score 会改变 lazy state，正在补实际 facts producer 到 Java consumer；M6 闭 phase/terminal 调用来源，保留 stamp 不能独自授效果；M7 与 writer/SAVE/动态 callback 同步首 SAVE 后的新绑定。M0 fullPower/完整 terms、M1 persistent writer、M2 动态 AST/VFS invalidation、M3 自然 episode、M4 实际资金、M5 战略选择、M6 实际终态、M7 实机 cold 链仍有缺口。各 owner source-map 保存精确证据和未执行范围，原生静态研究不授业务 PASS。

新发现的真实迁移缺口包括 Family actor-shadow 被错当第六公开角色、transport 写成功后读失败被错判零提交、Native/FIRST publisher 把外层 reservation 误要求为 hard Job，以及 `.4` WarEntry serializer 仍报 `.2` 来源。修复分别归共享 producer/consumer owner，当前 Native32 冻结图不热插后继。

**完整迁移未完成；第二次 Full35 编译、Native32 ENV/configure/build/fixture、完整 CI step、独立进程 SDK continuation、完整 Root/Game 和新自动游玩尚未执行。G2 完整验收仍为 0/8；Java 新增保存游戏日仍为 0。**

## 存储与现场

预算原件在上述 R3 的 `budget_fast_lane/`：`SOURCE-ADMISSION01.json`、`ROOT-TOOLS-CAPACITY01.json`、`ROOT-TOOLS-STANDING01.json` 和各独立 scope/supplement。56 source owner 共用 96 MiB 有限池；新 R3 D 工作包上限 3328 MiB，source 池只计一次。C 盘低于策略安全余量，不授新构建/临时输出；Maven 仓库和临时写入沿已准入 D 根。旧 whole allocated 仍 null，没有物理回收信用，没有删除。

仓库文档由 `ROOT-Z-DOCS128K01.json` 限定新写峰值与期限。所有额度于 `2026-10-24T04:30Z` 复核，不自动续期。必要旧基线仍按原 `2026-10-30T16:30Z` 用途复核；本进度按 record 于 `2027-04-22` 复核。

本机实际共享 task bus 是 `Z:/.codex-task-bus`；旧 docs 字面 `D:/workspace/.codex-task-bus` 是历史空总线，首次误注册随后应行政关闭，不代表实际共享任务登记。Root 已在实际总线登记 `ck3-java-g2-resume56-r3-20261024` 并 poll/ack；实际 list 截面只有该 Root 是新鲜非 done 项，不能据陈旧记录推断全机进程已退出。

本轮未启动/注入/停止 CK3、未切 Steam、未截图或抢焦点、未执行游戏动作或 SAVE。达到完整迁移和真实可运行条件后，再做本机后台 Steam offline/机器授权/账号与独占准入，以完整规划器从 1066 罗贝尔执行真实后态、推进及成对 SAVE；不静默回 Python。

## 后继：C18 预准入 RED 与 C19

同机器 `2026-10-23T22:42:14.091610200Z`，C18 whole 命令外层退出 1：C16 `ControlBuild.readTypedLease` 把 generic owner override 硬编码为 8 GiB，拒绝本机实际保守占用上界对应的新预算。Maven 尚未启动，未生成 build receipt；原 stderr 在 `J/logs/build-java-tools172-firstcut18-r3-root.stderr.log`（此处 `J` 为上述一期根），不记为 Java 编译失败或 JUnit 失败。

共享生产修复另建 C19，保留必要的 owner/task、来源、期限、额度必要性和政策公式校验；不改 C18 冻结源、不伪改旧实占。四个回归使用真实失败/预算原件执行实际 reader。C16 既有完整 manual capacity 合同用于 bootstrap，未消费的 C18 唯一 Maven future 显式转给 C19，不走 Python fallback。

C19 `c19-source01/terminal.json` 已实际 PASS：outer/child 0、Job active 0、stop null、三个来源守卫 MATCH，child 4.0012861 s，峰值 204496896 B。源根 `D:/codex-ck3-demos/2026-10-24-sharedwire-tools177-source19-r3`，实际 218 源图 378019 B，SHA `35a542ee4b79b0acac312e05c23d5f79b56dc75213feaf246ef5471df187038d`。唯一 C19 完整 Maven verify 已启动，终态未消费前不授通过，也不启动 Native 并行构建。

并发复盘进一步将 Root 汇线的真实瓶颈拆给现有线程：Advance infrastructure、public executable catalog、Lifecycle factory、Army runtime inputs、peace war-entry bridge；总 DomainAssembly/Commands/HostCAS 仍归唯一 Root owner。事件分母发现的 discovery、portable evidence、source provenance 和完整 Catalog producer 也各归独立 owner，避免仅增加 enum 而无真实生产者。部分已交付任务保持空闲直到新独立工作或真实编译反馈，不虚报持续 56 running。

实际总线于 `2026-10-23T22:48:21.789517Z` 更新为 running、sequence 8261；误用 D 历史总线的自有登记已行政关闭。完整迁移、G2 完整验收和保存日边界仍不变。

## 后继：C19 实际 RED、Native05 源物化与知识资源

同机器 `xenoamess-full-tower-eb9d2c1186`，截至 `2026-10-23T23:21:44Z`：

- C19 whole 已结束，默认 Maven probe 0；Maven 1，241.5421493 s、Job active 0、stop null、峰值 1221427200 B，来源前后 MATCH。实际 558 tests / 1 failure / 15 errors / 0 skipped，542 passed。原件 `J/logs/build-java-tools177-firstcut19-r3.json`（106953 B，SHA `61842ccc09f8e02506c61c44b8bdc2c53c0934888e48b0386bfa6163886b7045`）。14 errors 来自新迁层夹具缺 parent，1 error 来自把 Maven 参数 fragment 当完整 argv；另 1 failure 暴露 stdio 已锁存 UNKNOWN 在真实 exit 0 后丢失。共享源码已各由唯一 owner 窄修，C20 219 源待实际验收；C19 未获 runtime 资格，仍使用 C16。
- Native05 是消费 C19 RED/Job0 后明确授权的独立 source 分支。实际 outer PASS、child 0 / 80.7408808 s / Job0，前后和 runtime MATCH；内部 guard PASS，manifest 5554，guarded/pre/post 均 5601，child 0 / 73.8730119 s / Job0。`J/build/resume-current-20261024-r3/native_combined_control05/NATIVE-SOURCE-ACTUAL.json` 为 6733890 B，SHA `de488a30d86c0d5f5c2f4b87fbaf51437fa8d1ae679f3047cd742bfd271d7a3f`；实际 5511 package / 5501 native / 10 sibling，request05 与原始来源匹配。只授冻结源物化，不授 ENV、编译、fixture 或 Game。
- 完整事件 Catalog 的 REQUEST03 已调用既有 Python 生产者一次内存量测：exit 0，2.1063872 s，原包与资源前后 SHA 相等。四 build、219 查询 key、Unicode 15.1.0；展开 10163604 B，gzip 1096205 B。原件 `J/logs/VANILLA-CATALOG-MEASUREMENT03.json`（35011 B，SHA `f2082d267b5488500bf0dab6779d63a8ef91dc620a66404023cee9f69d621288`）。包含真实未注册响应和 nested insertion order；旧 01/02 仅历史。gzip 资源尚未写入，等待唯一预算签发后一次 exclusive write/readback；Java 运行时无 Python fallback。

56 owner 槽位已建立；完成源交付的线程不冒充 active。Root 已复用 M2–M7、Army13、MAA、M5 家族 variants、WarCore 等 owner，接续有明确输入和停止条件的实际缺口。尚未进行第二 Full35、Native32 编译或完整 CI，G2 完整验收 0/8，新增保存游戏日 0。

## 后继：C20 whole PASS 与真实 Catalog 单资源

同机器 `xenoamess-full-tower-eb9d2c1186`，`2026-10-23T23:39:52.513050800Z` 的 C20 实际 receipt：`J/logs/build-java-tools178-firstcut20-r3.json`，109098 B，SHA `b498a646e2f47c4184ed5af9e0dabb699aada44e156c1615c782c673d25a1d02`。Root 已消费 outer 0、status PASS/error null、source 与 compiled source MATCH；默认 Maven 3.10.0 probe 0，Maven 0 / 251.0705087 s / peak 1171722240 B / Job0 / stop null。79 份实际 JUnit XML 共 562 tests、0 failures、0 errors、0 skipped；六份完整部署已生成。独立 own-archive 尚未运行前，不据此替换 C16 资格。

Catalog 最终捕获07已实际 PASS（3.1209228 s）；仅一个 gzip 1096205 B，SHA `016aae559ae5c6f2843c65d166769703cd4bd37ce4986083b96de3fcc785bdfe`，原生产者全 summary 等于 measurement03。held handle FileID `562949966048287`、volume `6505083400996699863`、creation FILETIME `134372719154140270` 均为原生十进制字符串；gzip 与展开内容读回匹配。原件 `J/logs/VANILLA-CATALOG-CAPTURE07.json`，37234 B，SHA `676c34cc22f27e8804137ec11bc2288fc5bf83d08253ca3a1b5df7298af9d581`。04/05/06 的命令传输失败均发生于执行长度/语法先验，资源当时不存在；小日志保留，未覆写。唯一 data joint 实测保守上界 1163264 B，低于补卡1191936 B；无物理回收信用。

完整 Catalog Java provider 图已封；仍须真实安装及全消费者验收。Root 汇线另实查出漏装 succession/active-combat policy、缺实际 claims/derived-child authority、换 Game 的 checkpoint verifier 绑定、FIRST 物理恢复等缺口，均由现有 owner 处理，不用占位补满阶段数。Native05 仍仅 source PASS，ENV 尚未执行：共享旧 stage 合同错误地要求 ENV 提供 REGISTER 的全 Python 树，独立 C21 修复与回归正在准备。完整迁移与 Game 边界不变。

## 后继：C20 独立资格与 Full35 Input08 物化

同机器 `xenoamess-full-tower-eb9d2c1186`，C20 独立 own-archive compile/read 均实际 PASS；read child 0 / 81.1758115 s / Job0，三个守卫 MATCH。实际证明 `J/build/resume-current-20261024-r3/g2-m4/tools_c15/c20-reader-run01/actual.json` 为 14150 B，SHA `7608d5cd0c4b59db949e464a49084acc1c3627ba0fc26370155b40fc168138cd`。C20 已接管工具运行资格，范围仅 tools runtime，不授 HTTP、SDK、Native 或 Game。C21 stage 合同修复仅 source PASS；whole 尚未运行。只读 Git object 对比发现远端 `68c6f7e0353dbbe5d60726e21cce3ef1fc38b4e8` 另含 Maven 下载临时文件修复，须在 C22 后继保全并实际重验，不能用旧 C20 整树覆盖；当前 Z 工作区 119 项既有改动及 index 均未由本次工具集成改写。

Full35 Input07 因 owner 表误将 action-coordinator 标为 source-graph，被真实 Assembly 拒绝，原 RED 保留。Input08 仅纠正该 owner 后，Assembly、Plan 均 PASS。`2026-10-24T00:26:15.105905100Z`，物化实际 outer/child 0、184.3191366 s、peak 325488640 B、Job0、stop null，输入前后与 runtime 三守卫 MATCH。终态 `J/build/resume-current-20261024-r3/source_graph-full35-input08/commands/materialize/source03_audit/full35-materialize08/terminal.json` 为 110911 B，SHA `eebd639b83faffe29732c8e619d5db8094b793467362911a57a6fa54a6224119`；producer `materialization/SOURCE-GRAPH-ACTUAL01.json` 为 2430 B，SHA `22dc6348cecc41fe07b77e45824dc05fdcacb55b260da9b36d052a806aa117de`。新冻结根 `D:/codex-ck3-demos/2026-10-24-java-g2-source09-r3` 含 34 子模块、35 reactor projects，仅 SOURCE_ONLY；独立审计和第二次编译尚未执行。

六个 NEXT 领域 owner 已重新激活，共用 Root 私有铸造的真实首 SAVE/BASELINE/M7 proof；连续 domain import 不得抹去旧 UNKNOWN 与 journal。M1–M7 按明确有限前沿恢复研究，M0 正补当前 pending 产品；完成分支按真实需要复用，不维持虚假 56 running。实际 task bus sequence 8264 于 `2026-10-24T00:26:04.959573Z` 更新。G2 完整验收仍 0/8，新增保存游戏日仍 0。

独立审计08随后实际 PASS：22 个负例、manifest/native roundtrip 均 MATCH。第二 Full35 编译于 `2026-10-24T00:42:04.353738200Z` 实际 RED，默认 Maven 3.10.0，22 SUCCESS / 1 FAILURE / 12 SKIPPED，测试未执行；Maven exit1 / 93.0770089 s / Job0，source 与 compiled source MATCH。原件 `J/logs/build-full35-secondcompile08-r3-compile-only.json` 为 2370163 B，SHA `48938302f3cdf5bee6b2e0d9f01a603fe523052260dcf92b82e7764f11e0c3c4`。失败在 `DecisionMetricsRegression` 六处旧调用；实查还发现 selected production adapter 漏接已有 metrics instrumentation，已由唯一 owner 封两文件共享修复，保留强 deadline authority、CAS 和 UNKNOWN，不增加弱兼容接口。第三切面仅计划，未执行。

C22 source 实际 PASS：223 源、182 tools / 41 host，child0 / 3.1150306 s / Job0、三守卫 MATCH。actual `D:/codex-ck3-demos/2026-10-24-sharedwire-tools182-source22-r3/SOURCE-MAP01.json` 为 394174 B，SHA `27ecc9268dc24beb15564daea7e087a9dc382cf595e88bbc67abbc5ab0a016b4`。完整 Maven verify 已启动，未消费终态前仍用 qualified C20。当前另以唯一共享 contracts facade 补七项实际 receive semantic normalizer，接全生产者、指纹、Driver、归档及消费者；各叶子源码存在不授迁移通过。`2026-10-24T00:52:27.714151Z` task bus sequence8265；fresh remote 与 narrow fetch 均核 master 为 `68c6f7e0353dbbe5d60726e21cce3ef1fc38b4e8`。主 HEAD/index/119 项工作区改动未由工具集成改写。


## 后继：C22 完整工具资格与 Native 辅助编译

`machine_id: xenoamess-full-tower-eb9d2c1186`，观察 `2026-10-24T01:37:44Z`。C22 whole 实际 PASS：默认 Maven 3.10.0，82 套件共 587 tests，0 failure/error/skipped；Maven exit0 / 268.4976134 s / peak1188147200 B / Job0 / stop null，source/compiled source MATCH。原件 `J/logs/build-java-tools182-firstcut22-r3.json`（111478 B，SHA `1340c844046da2a3c6b137c625d681b71298997f6128f96821c87e1a8c72ea2e`）。独立 own-reader 实际 child0 / 55.2804366 s / Job0 / 三 MATCH；actual `J/build/resume-current-20261024-r3/g2-m4/tools_c15/c22-reader-run01/actual.json`（14150 B，SHA `e6648b71c0e653bd707c6db5c40ce28c9c33b850b524484acf1d108c2f637da5`）。C22 已接管工具运行资格，仅 tools 范围；182 是源文件数，非 MCP 工具数。正式交付 `R3/tools_c15/ACCEPTED-DELIVERY22.json`（13940 B，SHA `8d47770ba78d17209296786cae7d129cd32b2486b0bcb2ad41c2ee6252e6876b`）。

Native helper15 于 `2026-10-24T01:34:14Z` 严格 javac 实际 PASS，child0 / 1.297067 s / peak247279616 B / Job0，三个守卫 MATCH；19 真 class 共84305 B。终态 `J/build/resume-current-20261024-r3/native_combined_control05/env-qualification05/commands/reference_main/c22-native-helper-compile15/terminal.json`（22898 B，SHA `3191272d54f66f1e8a4eb979a4af9163cd5861b8f501a6b3235d0cc33ac7a3cf`）。ENV、32 native targets、35 runs、完整35 reactor测试与独立 SDK 尚未验收。

首次保存、恢复、NEXT 的真实 producer/全部领域消费者仍在接线。新发现原公共工具旧320目录漏了条件注册模块的至少3项，完整分母待真实 registration 调用图重建；旧320仅保历史。共享七项语义已封源，legacy WAL/cold payload完整规范化仍在迁移，不能以现代decode或空Seed代替。G2 M0–M7 完整实机验收 0/8，Java 新增保存日0，未启动 Game。

存储纠正：tools旧3.5MiB帽下的native实占超额保留为失败记录，后继4MiB仅面向后续有限峰值；auto-loop与M1/M2子帽亦保留logical/charged差异，无删除或追认PASS。56精确owner根已做有限Win32 census，不重复扫描旧J。Cygwin Python的机器fallback后缀不同于Windows原生机器ID，不代表换机；本轮Windows CPython实际仍为eb9d2c1186。task bus已消费至sequence8267。
